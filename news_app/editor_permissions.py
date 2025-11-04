"""Access control decorators and mixins for
 the news app editor functionality."""

from functools import wraps
from django.shortcuts import redirect
from django.contrib import messages
from django.contrib.auth.decorators import user_passes_test
from django.contrib.auth.mixins import UserPassesTestMixin, LoginRequiredMixin


def is_editor_or_in_editor_group(user):
    """Check if user has editor role or is in editor group."""
    if not user.is_authenticated:
        return False

    # Check if user has editor role
    if hasattr(user, 'role') and user.role == 'editor':
        return True

    # Check if user is in editor group
    if user.groups.filter(name='Editor').exists():
        return True

    # Check if user has the specific permission to approve articles
    if user.has_perm(
        'news_app.approve_article'
    ):
        return True

    # Check if user is superuser or staff (fallback)
    if user.is_superuser or user.is_staff:
        return True

    return False


def editor_required(function=None, login_url='login'):
    """
    Decorator for views that checks that the user is an editor.

    Usage:
        @editor_required
        def my_view(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def _wrapped_view(request, *args, **kwargs):
            # First check if user is logged in
            if not request.user.is_authenticated:
                messages.warning(
                    request,
                    "Please login to access the editor area."
                )
                return redirect(login_url)

            # Then check if user has editor permissions
            if not is_editor_or_in_editor_group(request.user):
                messages.error(
                    request,
                    "Access denied. Editor role or Editor group "
                    "membership required."
                )
                return redirect('article_list')

            return view_func(request, *args, **kwargs)
        return _wrapped_view

    if function:
        return decorator(function)
    return decorator


def editor_or_staff_required(function=None):
    """
    Decorator that requires user to be editor, staff, or superuser.
    More permissive than editor_required.
    """
    def test(user):
        return (
            user.is_authenticated and (
                is_editor_or_in_editor_group(user) or
                user.is_staff or
                user.is_superuser
            )
        )

    if function:
        return user_passes_test(test)(function)
    return user_passes_test(test)


class EditorRequiredMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    Class-based view mixin that requires editor permissions.

    Usage:
        class MyView(EditorRequiredMixin, ListView):
            ...
    """

    def test_func(self):
        """Test if user has editor permissions."""
        return is_editor_or_in_editor_group(self.request.user)

    def handle_no_permission(self):
        """Handle users without permission."""
        if not self.request.user.is_authenticated:
            messages.warning(
                self.request,
                "Please log in to access the editor area."
            )
            return redirect('login')
        else:
            messages.error(
                self.request,
                "Access denied. Editor role or Editor group "
                "membership required."
            )
            return redirect('article_list')


class EditorOrStaffMixin(LoginRequiredMixin, UserPassesTestMixin):
    """
    More permissive mixin that allows editors, staff, or superusers.
    """

    def test_func(self):
        """Test if user has editor or staff permissions."""
        user = self.request.user
        return (
            is_editor_or_in_editor_group(user) or
            user.is_staff or
            user.is_superuser
        )

    def handle_no_permission(self):
        """Handle users without permission."""
        if not self.request.user.is_authenticated:
            messages.warning(
                self.request,
                "Please log in to access this area."
            )
            return redirect('login')
        else:
            messages.error(
                self.request,
                "Access denied. Editor, staff, or admin "
                "privileges required."
            )
            return redirect('article_list')


def check_article_edit_permission(user, article):
    """
    Check if user has permission to edit/approve a specific article.

    Rules:
    - Editors can approve any article
    - Staff/superuser can approve any article
    - Users in Editor group can approve any article
    - Article authors cannot approve their own articles (conflict of interest)

    Returns: (has_permission: bool, reason: str)
    """
    if not user.is_authenticated:
        return False, "User not authenticated"

    # Check if user is trying to approve their own article
    if article.author == user:
        return False, "Authors cannot approve their own articles"

    # Check editor permissions
    if is_editor_or_in_editor_group(user):
        return True, "User has editor permissions"

    # Check staff permissions
    if user.is_staff or user.is_superuser:
        return True, "User has staff/admin permissions"

    return False, "User lacks editor permissions"


def article_approval_permission_required(view_func):
    """
    Decorator specifically for article approval views.
    Includes additional checks like preventing self-approval.
    """
    @wraps(view_func)
    def _wrapped_view(request, *args, **kwargs):
        # First check basic editor permissions
        if not request.user.is_authenticated:
            messages.warning(
                request,
                "Please log in to access the editor area."
            )
            return redirect('login')

        if not is_editor_or_in_editor_group(request.user):
            messages.error(
                request,
                "Access denied. Editor role or Editor group "
                "membership required."
            )
            return redirect('article_list')

        # If there's an article_id in the URL, check specific permissions
        article_id = kwargs.get('article_id') or kwargs.get('pk')
        if article_id:
            # pylint: disable=import-outside-toplevel
            # Import here to avoid circular imports
            from .models import Article
            try:
                # pylint: disable=no-member
                article = Article.objects.get(
                    id=article_id
                )
                has_permission, reason = check_article_edit_permission(
                    request.user,
                    article
                )

                if not has_permission:
                    messages.error(
                        request,
                        f"Permission denied: {reason}"
                    )
                    return redirect('editor_dashboard')
            except Article.DoesNotExist:  # pylint: disable=no-member
                messages.error(
                    request,
                    "Article not found."
                )
                return redirect('editor_dashboard')

        return view_func(request, *args, **kwargs)

    return _wrapped_view
