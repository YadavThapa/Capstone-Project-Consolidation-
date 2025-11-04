"""Enhanced admin views for access control and article approval management."""

from typing import Any

from django.contrib import messages
from django.contrib.admin.views.decorators import staff_member_required
from django.contrib.auth import authenticate
from django.contrib.auth.decorators import user_passes_test
from django.db.models import Q
from django.http import JsonResponse
from django.shortcuts import get_object_or_404, redirect, render
from django.utils import timezone
from django.views.decorators.http import require_POST

from .models import Article, CustomUser, Notification, Publisher


# Helper to obtain a model manager in a way that static type checkers
# recognize.
def get_manager(model: Any):
    """
    Return the default manager for the given Django model in a safe way.
    Falls back to _default_manager if 'objects' is not defined.
    """
    return getattr(model, "objects", getattr(model, "_default_manager", None))


def is_admin_or_editor(user):
    """
    Predicate used by user_passes_test to allow access to admins and editors.
    Returns True if the user is authenticated and is a superuser, staff,
    or has role 'editor'.
    """
    if user is None:
        return False
    # Use getattr to avoid AttributeError if CustomUser is not yet fully
    # loaded in some contexts
    return bool(
        getattr(user, "is_authenticated", False)
        and (
            getattr(user, "is_superuser", False)
            or getattr(user, "is_staff", False)
            or getattr(user, "role", None) == "editor"
        )
    )


def admin_access_check(request):
    """
    Custom view to check admin access permissions.
    Redirects regular users with warning message.
    """
    if not request.user.is_authenticated:
        # Not logged in - redirect to login with next parameter
        messages.warning(
            request,
            "Please log in first. Admin area is only for Staff or Admin role."
        )
        return redirect("login")

    if not (request.user.is_staff or request.user.is_superuser):
        # Regular user trying to access admin
        messages.error(
            request,
            "It is only for Staff or Admin role. "
            "Please try to log in with Login or Signup.",
        )
        return redirect("article_list")

    # User has permission, redirect to actual admin
    return redirect("/django-admin/")


def protected_admin_login(request):
    """
    Custom admin login view with role checking.
    """
    if request.method == "POST":
        username = request.POST.get("username")
        password = request.POST.get("password")

        if username and password:
            user = authenticate(username=username, password=password)
            if user is not None:
                if not (user.is_staff or user.is_superuser):
                    messages.error(
                        request,
                        "It is only for Staff or Admin role. "
                        "Please try to log in with Login or Signup.",
                    )
                    return redirect("article_list")


@staff_member_required
def admin_dashboard(request):
    """Admin dashboard showing article approval overview."""

    # Get article statistics
    total_articles = get_manager(Article).count()
    approved_articles = get_manager(Article).filter(is_approved=True).count()
    pending_articles = (
        get_manager(Article)
        .filter(is_approved=False, status="pending")
        .count()
    )
    rejected_articles = (
        get_manager(Article)
        .filter(is_approved=False, status="rejected")
        .count()
    )

    # Get recent pending articles for approval
    pending_for_approval = (
        get_manager(Article)
        .filter(is_approved=False, status="pending")
        .select_related("author", "publisher")
        .order_by("-created_at")[:10]
    )

    # Get recently approved articles
    recently_approved = (
        get_manager(Article)
        .filter(is_approved=True, approved_at__isnull=False)
        .select_related("author", "publisher", "approved_by")
        .order_by("-approved_at")[:10]
    )

    # Get user statistics
    total_users = CustomUser.objects.count()
    journalists = CustomUser.objects.filter(role="journalist").count()
    editors = CustomUser.objects.filter(role="editor").count()
    readers = CustomUser.objects.filter(role="reader").count()

    # Get publisher statistics
    total_publishers = get_manager(Publisher).count()

    context = {
        "total_articles": total_articles,
        "approved_articles": approved_articles,
        "pending_articles": pending_articles,
        "rejected_articles": rejected_articles,
        "pending_for_approval": pending_for_approval,
        "recently_approved": recently_approved,
        "total_users": total_users,
        "journalists": journalists,
        "editors": editors,
        "readers": readers,
        "total_publishers": total_publishers,
        "recent_articles": (
            get_manager(Article)
            .select_related("author", "publisher")
            .order_by("-created_at")[:5]
        ),
    }

    return render(request, "news_app/admin/admin_dashboard.html", context)


@staff_member_required
def article_approval_list(request):
    """List view for article approval management."""

    # Filter parameters
    status_filter = request.GET.get("status", "pending")
    author_filter = request.GET.get("author", "")
    publisher_filter = request.GET.get("publisher", "")
    search_query = request.GET.get("q", "")

    # Base queryset - show all articles including non-approved ones
    articles = (
        get_manager(Article)
        .select_related("author", "publisher", "approved_by")
    )

    # Apply filters
    if status_filter == "pending":
        articles = articles.filter(is_approved=False)
    elif status_filter == "approved":
        articles = articles.filter(is_approved=True)
    elif status_filter == "draft":
        articles = articles.filter(status="draft")
    elif status_filter == "rejected":
        articles = articles.filter(status="rejected")

    if author_filter:
        articles = articles.filter(author__username__icontains=author_filter)

    if publisher_filter:
        articles = articles.filter(publisher__name__icontains=publisher_filter)

    if search_query:
        articles = articles.filter(
            Q(title__icontains=search_query)
            | Q(content__icontains=search_query)
            | Q(summary__icontains=search_query)
        )

    articles = articles.order_by("-created_at")

    # Get filter options
    authors = CustomUser.objects.filter(role="journalist").order_by("username")
    publishers = get_manager(Publisher).order_by("name")
    context = {
        "articles": articles,
        "authors": authors,
        "publishers": publishers,
        "status_filter": status_filter,
        "author_filter": author_filter,
        "publisher_filter": publisher_filter,
        "search_query": search_query,
    }

    return render(
        request,
        "news_app/admin/article_approval_list.html",
        context
    )


@user_passes_test(is_admin_or_editor)
@require_POST
def approve_article_admin(request, article_id):
    """Admin approve article action."""

    article = get_object_or_404(Article, id=article_id)

    if article.is_approved:
        return JsonResponse(
            {"success": False, "message": "Article is already approved."}
        )

    # Approve the article
    article.is_approved = True
    article.status = "approved"
    article.approved_by = request.user
    article.approved_at = timezone.now()
    article.save()

    # Create notification for the author
    get_manager(Notification).create(
        recipient=article.author,
        title=f'Your article "{article.title}" has been approved',
        message=(
            f"Your article has been approved by "
            f"{request.user.get_full_name() or request.user.username} "
            "and is now published."
        ),
        notification_type="article_approved",
        article=article,
    )

    messages.success(
        request, f'Article "{article.title}" has been approved successfully.'
    )

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse(
            {
                "success": True,
                "message": "Article approved successfully.",
                "approved_by": (
                    request.user.get_full_name() or request.user.username
                ),
                "approved_at": (
                    article.approved_at.strftime("%B %d, %Y at %I:%M %p")
                ),
            }
        )

    return redirect("admin_article_approval_list")


@user_passes_test(is_admin_or_editor)
@require_POST
def reject_article_admin(request, article_id):
    """Admin reject article action."""

    article = get_object_or_404(Article, id=article_id)
    rejection_reason = request.POST.get("reason", "No reason provided")

    # Update article status
    article.status = "rejected"
    article.is_approved = False
    article.save()

    # Create notification for the author
    get_manager(Notification).create(
        recipient=article.author,
        title=f'Your article "{article.title}" needs revision',
        message=(
            f"Your article has been rejected by "
            f"{request.user.get_full_name() or request.user.username}. "
            f"Reason: {rejection_reason}"
        ),
        notification_type="article_rejected",
        article=article,
    )

    messages.warning(request, f'Article "{article.title}" has been rejected.')

    if request.headers.get("X-Requested-With") == "XMLHttpRequest":
        return JsonResponse(
            {
                "success": True,
                "message": "Article rejected successfully.",
                "rejection_reason": rejection_reason,
            }
        )

    return redirect("admin_article_approval_list")


@staff_member_required
def article_detail_admin(request, article_id):
    """Detailed view of article for admin review."""

    # Use the model manager to avoid accessing protected members
    article = get_object_or_404(
        get_manager(Article)
        .select_related("author", "publisher", "approved_by"),
        id=article_id,
    )

    context = {
        "article": article,
        "can_edit": True,  # Admins can always edit
    }

    return render(request, "news_app/admin/article_detail_admin.html", context)
