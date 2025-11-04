"""Simplified views for the news app - Core functionality only."""
import logging
from django.shortcuts import render, get_object_or_404, redirect
from django.contrib import messages
from django.contrib.auth import get_user_model, login
from django.contrib.auth.decorators import login_required
from django.views.decorators.http import require_POST
from django.db.models import Q
from .forms import ContactForm, CustomUserCreationForm, ProfileEditForm
from .models import Article, ContactMessage, Notification, Publisher, Category
# pylint: disable=no-member  # Django models have 'objects' manager
logger = logging.getLogger(__name__)


def article_list(request):

    """
    Display list of published articles on homepage with category filtering.
    Args:
        request: Django HttpRequest object.
    Returns:
        Rendered homepage with articles and categories.
    """
    try:
        # Get all active categories for navigation
        categories = Category.objects.filter(
            is_active=True
        ).order_by('order')

        # Base queryset for all articles
        all_articles = Article.objects.filter(
            status='approved',
            is_approved=True
        ).select_related(
            'author', 'publisher', 'category'
        ).order_by('-published_at')

        # Get category filter from URL parameters
        category_slug = request.GET.get('category', '')
        search_query = request.GET.get('q', '')
        selected_category = None

        # Apply category filter if specified
        if category_slug:
            try:
                selected_category = Category.objects.get(
                    slug=category_slug, is_active=True
                )
                all_articles = all_articles.filter(category=selected_category)
            except Category.DoesNotExist:
                # If category doesn't exist, show all articles
                pass

        # Apply search filter if specified
        if search_query:
            all_articles = all_articles.filter(
                Q(title__icontains=search_query) |
                Q(summary__icontains=search_query) |
                Q(content__icontains=search_query) |
                Q(author__username__icontains=search_query) |
                Q(publisher__name__icontains=search_query)
            )

        # If user is authenticated and is reader, prioritize subscribed content
        subscribed_articles = []
        user_is_reader = (
            request.user.is_authenticated and
            hasattr(request.user, 'role') and
            request.user.role == 'reader'
        )
        if user_is_reader:
            # Get articles from subscribed publishers and journalists
            subscribed_articles = all_articles.filter(
                Q(publisher__in=request.user.subscribed_publishers.all()) |
                Q(author__in=request.user.subscribed_journalists.all())
            ).distinct()[:10]

        # Get remaining articles (excluding subscribed ones)
        remaining_articles = all_articles.exclude(
            id__in=[article.id for article in subscribed_articles]
        )[:15]

        # Combine articles (subscribed first, then others)
        articles = list(subscribed_articles) + list(remaining_articles)

        # Get publishers for sidebar
        publishers = Publisher.objects.all().order_by('name')[:10]

        context = {
            'articles': articles[:25],  # Limit to 25 total
            'subscribed_articles': subscribed_articles,
            'has_subscriptions': len(subscribed_articles) > 0,
            'publishers': publishers,
            'categories': categories,
            'selected_category': selected_category,
            'category_slug': category_slug,
            'search_query': search_query,
        }

        return render(request, 'news_app/article_list.html', context)
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error("Error in article_list view: %s", str(e))
        return render(request, 'news_app/article_list.html', {'articles': []})


def article_detail(request, slug):
    """
    Display individual article details.
    Args:
        request: Django HttpRequest object.
        slug: Slug of the article to display.
    Returns:
        Rendered article detail page.
    """
    try:
        article = get_object_or_404(
            Article.objects.select_related('author', 'publisher'),
            slug=slug,
            status='approved',
            is_approved=True
        )

        # Get related articles (same author or similar topics)
        related_articles = Article.objects.filter(
            status='approved',
            is_approved=True
        ).exclude(id=article.id).order_by('-published_at')[:5]

        context = {
            'article': article,
            'related_articles': related_articles,
        }

        return render(request, 'news_app/article_detail.html', context)
    except Exception as e:  # pylint: disable=broad-exception-caught
        logger.error(
            "Error in article_detail view for slug %s: %s", slug, str(e)
        )
        messages.error(request, 'Article not found.')
        return render(request, 'news_app/article_list.html', {'articles': []})


def about(request):
    """
    Display about page.
    """
    return render(request, 'news_app/about.html')


def contact(request):
    """
    Handle contact form submissions.
    Args:
        request: Django HttpRequest object.
    Returns:
        Rendered contact page or redirects after form submission.
    """
    if request.method == 'POST':
        form = ContactForm(request.POST)
        if form.is_valid():
            try:
                # Save contact message
                contact_message = ContactMessage.objects.create(
                    **form.cleaned_data
                )

                # Create notifications for admin users
                user_model = get_user_model()
                admin_users = user_model.objects.filter(
                    Q(is_staff=True) | Q(is_superuser=True)
                )

                # Create message preview
                msg_preview = contact_message.message[:100]
                if len(contact_message.message) > 100:
                    msg_preview += '...'

                for admin_user in admin_users:
                    notification_message = (
                        f"You have received a new contact message from "
                        f"{contact_message.name} ({contact_message.email}). "
                        f"Message preview: {msg_preview}"
                    )

                    Notification.objects.create(
                        recipient=admin_user,
                        title=f"New Contact Message from "
                              f"{contact_message.name}",
                        message=notification_message
                    )

                messages.success(
                    request,
                    'Thanks — your message has been sent. '
                    'Our team will get back to you soon!'
                )
                contact_form = ContactForm()
                return render(request, 'news_app/contact.html',
                              {'form': contact_form})

            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error("Error saving contact message: %s", str(e))
                messages.error(
                    request,
                    'Sorry, there was an error sending your message. '
                    'Please try again later.'
                )
    else:
        form = ContactForm()

    return render(request, 'news_app/contact.html', {'form': form})


def signup(request):
    """
    Handle user registration.
    Args:
        request: Django HttpRequest object.
    Returns:
        Rendered signup page or redirects after successful registration.
    """
    if request.method == 'POST':
        form = CustomUserCreationForm(request.POST)
        if form.is_valid():
            try:
                user = form.save()
                # Automatically log in the user after successful registration
                login(request, user)
                messages.success(
                    request,
                    f'Welcome {user.username}! Your account has been created '
                    'successfully.'
                )
                # Redirect to homepage after successful signup
                log_msg = "User %s created successfully, redirecting"
                logger.info(log_msg, user.username)
                return redirect('article_list')
            except Exception as e:  # pylint: disable=broad-exception-caught
                logger.error("Error creating user account: %s", str(e))
                messages.error(
                    request,
                    'There was an error creating your account. '
                    'Please try again.'
                )
        else:
            # Form is not valid - show form errors
            logger.warning("Signup form validation failed: %s", form.errors)
            messages.error(
                request,
                'Please correct the errors below and try again.'
            )
    else:
        form = CustomUserCreationForm()

    return render(request, 'registration/signup.html', {'form': form})


@login_required
def publisher_list(request):
    """Display list of all publishers - Login required."""
    publishers = Publisher.objects.all().order_by('name')
    template_name = 'news_app/publisher_list.html'
    return render(request, template_name, {'publishers': publishers})


def publisher_detail(request, pk):
    """Display publisher details, staff, and their articles."""
    publisher = get_object_or_404(Publisher, pk=pk)
    articles = Article.objects.filter(
        publisher=publisher,
        status='approved',
        is_approved=True
    ).select_related('author').order_by('-published_at')[:10]

    # Get staff information
    editors = publisher.get_editors().select_related()
    journalists = publisher.get_journalists().select_related()

    # Check if user is subscribed to this publisher
    is_subscribed = False
    user_is_auth = request.user.is_authenticated
    has_subscriptions = hasattr(request.user, 'subscribed_publishers')
    if user_is_auth and has_subscriptions:
        is_subscribed = publisher in request.user.subscribed_publishers.all()

    context = {
        'publisher': publisher,
        'articles': articles,
        'editors': editors,
        'journalists': journalists,
        'is_subscribed': is_subscribed,
    }
    return render(request, 'news_app/publisher_detail.html', context)


@login_required
def journalist_list(request):
    """Display list of all journalists - Login required."""
    user_model = get_user_model()
    journalists = user_model.objects.filter(
        role='journalist'
    ).order_by('username')
    template_name = 'news_app/journalist_list.html'
    return render(request, template_name, {'journalists': journalists})


def journalist_detail(request, pk):
    """Display journalist details and their articles."""
    user_model = get_user_model()
    journalist = get_object_or_404(user_model, pk=pk, role='journalist')
    articles = Article.objects.filter(
        author=journalist,
        status='approved',
        is_approved=True
    ).order_by('-published_at')[:10]

    # Check if user is subscribed to this journalist
    is_subscribed = False
    user_is_auth = request.user.is_authenticated
    has_subscriptions = hasattr(request.user, 'subscribed_journalists')
    if user_is_auth and has_subscriptions:
        is_subscribed = journalist in request.user.subscribed_journalists.all()

    context = {
        'journalist': journalist,
        'articles': articles,
        'is_subscribed': is_subscribed,
    }
    return render(request, 'news_app/journalist_detail.html', context)


@login_required
@require_POST
def toggle_publisher_subscription(request, pk):
    """Toggle subscription to a publisher."""
    publisher = get_object_or_404(Publisher, pk=pk)
    user = request.user

    # Only readers can subscribe
    if user.role != 'reader':
        messages.error(request, 'Only readers can subscribe to publishers.')
        return redirect('publisher_detail', pk=pk)

    if publisher in user.subscribed_publishers.all():
        user.subscribed_publishers.remove(publisher)
        messages.success(request, f'Unsubscribed from {publisher.name}.')
    else:
        user.subscribed_publishers.add(publisher)
        messages.success(request, f'Subscribed to {publisher.name}.')

    return redirect('publisher_detail', pk=pk)


@login_required
@require_POST
def toggle_journalist_subscription(request, pk):
    """Toggle subscription to a journalist."""
    user_model = get_user_model()
    journalist = get_object_or_404(user_model, pk=pk, role='journalist')
    user = request.user

    # Only readers can subscribe
    if user.role != 'reader':
        messages.error(request, 'Only readers can subscribe to journalists.')
        return redirect('journalist_detail', pk=pk)

    if journalist in user.subscribed_journalists.all():
        user.subscribed_journalists.remove(journalist)
        name = journalist.get_full_name() or journalist.username
        messages.success(request, f'Unsubscribed from {name}.')
    else:
        user.subscribed_journalists.add(journalist)
        name = journalist.get_full_name() or journalist.username
        messages.success(request, f'Subscribed to {name}.')

    return redirect('journalist_detail', pk=pk)


@login_required
def profile(request):
    """Display user profile and manage subscriptions."""
    user = request.user
    has_pub_subs = hasattr(user, 'subscribed_publishers')
    subscribed_publishers = (user.subscribed_publishers.all()
                             if has_pub_subs else [])
    has_journ_subs = hasattr(user, 'subscribed_journalists')
    subscribed_journalists = (user.subscribed_journalists.all()
                              if has_journ_subs else [])

    # Get user's managed content if they are a journalist
    managed_articles = []
    managed_publisher = None
    if user.role == 'journalist':
        article_query = Article.objects.filter(author=user)
        managed_articles = article_query.order_by('-created_at')[:5]
        managed_publisher = user.publisher

    context = {
        'user': user,
        'subscribed_publishers': subscribed_publishers,
        'subscribed_journalists': subscribed_journalists,
        'managed_articles': managed_articles,
        'managed_publisher': managed_publisher,
    }
    return render(request, 'news_app/profile.html', context)


@login_required
def edit_profile(request):
    """Allow users to edit their profile information."""
    if request.method == 'POST':
        form = ProfileEditForm(request.POST, request.FILES,
                               instance=request.user)
        if form.is_valid():
            form.save()
            messages.success(request,
                             'Your profile has been updated successfully!')
            return redirect('profile')
    else:
        form = ProfileEditForm(instance=request.user)

    context = {
        'form': form,
        'user': request.user,
    }
    return render(request, 'news_app/edit_profile.html', context)
