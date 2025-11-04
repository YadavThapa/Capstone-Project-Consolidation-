"""Editor-specific views for article review and approval system."""

from datetime import timedelta
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.views.decorators.http import require_POST, require_http_methods
from django.db.models import Q, Count
from django.utils import timezone
from django.core.paginator import Paginator
from django.db import transaction

from .models import Article, CustomUser, Publisher, Category
from .editor_permissions import (
    editor_required,
    article_approval_permission_required,
    check_article_edit_permission
)


@editor_required
def editor_dashboard(request):
    """
    Main dashboard for editors showing pending articles and statistics.
    """
    # Get pending articles count
    pending_articles = Article.objects.filter(  # pylint: disable=no-member
        status='pending',
        is_approved=False
    ).count()

    # Get articles approved today
    today = timezone.now().date()
    approved_today = Article.objects.filter(  # pylint: disable=no-member
        is_approved=True,
        approved_at__date=today
    ).count()

    # Get recent pending articles (last 10)
    recent_pending = Article.objects.filter(  # pylint: disable=no-member
        status='pending',
        is_approved=False
    ).select_related('author', 'publisher').order_by('-created_at')[:10]

    # Get articles by status for chart
    article_objects = Article.objects  # pylint: disable=no-member
    status_counts = {
        'pending': article_objects.filter(
            status='pending', is_approved=False
        ).count(),
        'approved': article_objects.filter(is_approved=True).count(),
        'rejected': article_objects.filter(status='rejected').count(),
        'draft': article_objects.filter(status='draft').count(),
    }

    # Get articles by publisher
    publisher_stats = Publisher.objects.annotate(  # pylint: disable=no-member
        total_articles=Count('articles'),
        pending_articles=Count('articles', filter=Q(
            articles__status='pending', articles__is_approved=False
        ))
    ).order_by('-total_articles')[:5]

    context = {
        'pending_count': pending_articles,
        'approved_today': approved_today,
        'recent_pending': recent_pending,
        'status_counts': status_counts,
        'publisher_stats': publisher_stats,
    }

    return render(request, 'news_app/editor/dashboard.html', context)


@editor_required
def editor_article_list(request):
    """
    List view for editors to see all articles with filtering and search.
    """
    # Base queryset
    articles = Article.objects.select_related(  # pylint: disable=no-member
        'author', 'publisher', 'category', 'approved_by'
    ).order_by('-created_at')

    # Get filter parameters
    status_filter = request.GET.get('status', '')
    search_query = request.GET.get('search', '')
    author_filter = request.GET.get('author', '')
    publisher_filter = request.GET.get('publisher', '')
    category_filter = request.GET.get('category', '')
    date_from = request.GET.get('date_from', '')
    date_to = request.GET.get('date_to', '')

    # Apply filters
    if status_filter:
        if status_filter == 'pending':
            articles = articles.filter(status='pending', is_approved=False)
        elif status_filter == 'approved':
            articles = articles.filter(is_approved=True)
        elif status_filter == 'rejected':
            articles = articles.filter(status='rejected')
        else:
            articles = articles.filter(status=status_filter)

    if search_query:
        articles = articles.filter(
            Q(title__icontains=search_query) |
            Q(content__icontains=search_query) |
            Q(summary__icontains=search_query) |
            Q(author__username__icontains=search_query) |
            Q(author__first_name__icontains=search_query) |
            Q(author__last_name__icontains=search_query)
        )

    if author_filter:
        articles = articles.filter(author_id=author_filter)

    if publisher_filter:
        articles = articles.filter(publisher_id=publisher_filter)

    if category_filter:
        articles = articles.filter(category_id=category_filter)

    if date_from:
        articles = articles.filter(created_at__date__gte=date_from)

    if date_to:
        articles = articles.filter(created_at__date__lte=date_to)

    # Pagination
    paginator = Paginator(articles, 12)  # 12 articles per page
    page_number = request.GET.get('page')
    page_obj = paginator.get_page(page_number)

    # Get filter options
    authors = CustomUser.objects.filter(  # pylint: disable=no-member
        role='journalist'
    ).order_by('username')
    publishers = Publisher.objects.all().order_by(  # pylint: disable=no-member
        'name'
    )
    categories = Category.objects.filter(  # pylint: disable=no-member
        is_active=True
    ).order_by('name')

    context = {
        'articles': page_obj,
        'authors': authors,
        'publishers': publishers,
        'categories': categories,
        'is_paginated': page_obj.has_other_pages(),
        'page_obj': page_obj,
        # Preserve filter values for form
        'current_filters': {
            'status': status_filter,
            'search': search_query,
            'author': author_filter,
            'publisher': publisher_filter,
            'category': category_filter,
            'date_from': date_from,
            'date_to': date_to,
        }
    }

    return render(request, 'news_app/editor/article_list.html', context)


@editor_required
def editor_article_detail(request, article_id):
    """
    Detailed view of an article for editor review.
    """
    article = get_object_or_404(Article, id=article_id)

    # Check if user can edit this article
    has_permission, reason = check_article_edit_permission(
        request.user, article
    )

    # Get similar articles (same category or author)
    similar_articles = Article.objects.filter(  # pylint: disable=no-member
        Q(category=article.category) | Q(author=article.author)
    ).exclude(id=article.id).order_by('-created_at')[:5]

    # Get article history (if available)
    # Note: This would require a more complex history tracking system
    # For now, we'll just show basic info

    context = {
        'article': article,
        'can_approve': has_permission,
        'permission_reason': reason,
        'similar_articles': similar_articles,
        'is_own_article': article.author == request.user,
    }

    return render(request, 'news_app/editor/article_detail.html', context)


@article_approval_permission_required
@require_POST
def approve_article(request, article_id):
    """
    Approve an article. Only editors can approve articles they didn't write.
    """
    article = get_object_or_404(Article, id=article_id)

    # Double-check permissions
    has_permission, reason = check_article_edit_permission(
        request.user, article
    )
    if not has_permission:
        messages.error(request, f"Cannot approve article: {reason}")
        return redirect('editor_article_detail', article_id=article_id)

    # Check if article is already approved
    if article.is_approved:
        messages.info(request, "Article is already approved.")
        return redirect('editor_article_detail', article_id=article_id)

    # Approve the article
    with transaction.atomic():
        article.is_approved = True
        article.status = 'approved'
        article.approved_by = request.user
        article.approved_at = timezone.now()

        # Set published date if not set
        if not article.published_at:
            article.published_at = timezone.now()

        article.save()

    messages.success(
        request,
        f'Article "{article.title}" has been approved and published.'
    )

    # Redirect based on source
    next_url = request.POST.get('next', 'editor_dashboard')
    return redirect(next_url)


@article_approval_permission_required
@require_POST
def reject_article(request, article_id):
    """
    Reject an article with optional reason.
    """
    article = get_object_or_404(Article, id=article_id)

    # Double-check permissions
    has_permission, reason = check_article_edit_permission(
        request.user, article
    )
    if not has_permission:
        messages.error(request, f"Cannot reject article: {reason}")
        return redirect('editor_article_detail', article_id=article_id)

    # Get rejection reason from form
    rejection_reason = request.POST.get('rejection_reason', '').strip()

    # Reject the article
    with transaction.atomic():
        article.is_approved = False
        article.status = 'rejected'
        article.approved_by = request.user
        article.approved_at = timezone.now()

        # Store rejection reason (you might want to add this field to model)
        # For now, we'll use a simple approach
        if rejection_reason:
            # You could create a rejection log or add a field to the model
            pass

        article.save()

    messages.success(
        request,
        f'Article "{article.title}" has been rejected.'
    )

    # Redirect based on source
    next_url = request.POST.get('next', 'editor_dashboard')
    return redirect(next_url)


@editor_required
@require_http_methods(["GET", "POST"])
def bulk_article_action(request):
    """
    Handle bulk actions on articles (approve multiple, reject multiple, etc.)
    """
    if request.method == 'POST':
        action = request.POST.get('action')
        article_ids = request.POST.getlist('article_ids')

        if not article_ids:
            messages.warning(request, "No articles selected.")
            return redirect('editor_article_list')

        # Get articles
        articles = Article.objects.filter(  # pylint: disable=no-member
            id__in=article_ids
        )

        success_count = 0
        error_count = 0

        for article in articles:
            # Check permission for each article
            has_permission, _ = check_article_edit_permission(
                request.user, article
            )

            if not has_permission:
                error_count += 1
                continue

            try:
                with transaction.atomic():
                    if action == 'approve':
                        if not article.is_approved:
                            article.is_approved = True
                            article.status = 'approved'
                            article.approved_by = request.user
                            article.approved_at = timezone.now()
                            if not article.published_at:
                                article.published_at = timezone.now()
                            article.save()
                            success_count += 1

                    elif action == 'reject':
                        if (article.is_approved or
                                article.status == 'pending'):
                            article.is_approved = False
                            article.status = 'rejected'
                            article.approved_by = request.user
                            article.approved_at = timezone.now()
                            article.save()
                            success_count += 1

                    elif action == 'mark_pending':
                        article.is_approved = False
                        article.status = 'pending'
                        article.approved_by = None
                        article.approved_at = None
                        article.save()
                        success_count += 1

            except Exception:  # pylint: disable=broad-exception-caught
                error_count += 1

        # Show results
        if success_count > 0:
            messages.success(
                request,
                f"Successfully processed {success_count} articles."
            )

        if error_count > 0:
            messages.warning(
                request,
                f"{error_count} articles could not be processed due to "
                "permission issues."
            )

    return redirect('editor_article_list')


@editor_required
def editor_statistics(request):
    """
    Statistics page for editors showing approval metrics.
    """
    # Get date range from request (default to last 30 days)
    end_date = timezone.now().date()
    start_date = end_date - timedelta(days=30)

    date_from = request.GET.get('date_from', start_date.strftime('%Y-%m-%d'))
    date_to = request.GET.get('date_to', end_date.strftime('%Y-%m-%d'))

    # Parse dates
    try:
        start_date = timezone.datetime.strptime(
            date_from, '%Y-%m-%d'
        ).date()
        end_date = timezone.datetime.strptime(date_to, '%Y-%m-%d').date()
    except ValueError:
        start_date = end_date - timedelta(days=30)
        end_date = timezone.now().date()

    # Get statistics
    article_objects = Article.objects  # pylint: disable=no-member
    stats = {
        'total_articles': article_objects.count(),
        'approved_articles': article_objects.filter(
            is_approved=True
        ).count(),
        'pending_articles': article_objects.filter(
            status='pending', is_approved=False
        ).count(),
        'rejected_articles': article_objects.filter(
            status='rejected'
        ).count(),
        'approved_in_period': article_objects.filter(
            approved_at__date__gte=start_date,
            approved_at__date__lte=end_date,
            is_approved=True
        ).count(),
        'rejected_in_period': article_objects.filter(
            approved_at__date__gte=start_date,
            approved_at__date__lte=end_date,
            status='rejected'
        ).count(),
    }

    # Get top approvers
    top_approvers = CustomUser.objects.filter(  # pylint: disable=no-member
        approved_articles__approved_at__date__gte=start_date,
        approved_articles__approved_at__date__lte=end_date
    ).annotate(
        approval_count=Count('approved_articles')
    ).order_by('-approval_count')[:5]

    # Get articles by category
    category_stats = Category.objects.annotate(  # pylint: disable=no-member
        total_articles=Count('articles'),
        approved_articles=Count(
            'articles', filter=Q(articles__is_approved=True)
        )
    ).order_by('-total_articles')[:10]

    context = {
        'stats': stats,
        'top_approvers': top_approvers,
        'category_stats': category_stats,
        'date_from': date_from,
        'date_to': date_to,
        'start_date': start_date,
        'end_date': end_date,
    }

    return render(request, 'news_app/editor/statistics.html', context)
