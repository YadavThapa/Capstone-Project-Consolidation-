"""Context processors for the news_app.

Provide small helpers used by templates (notifications badge/dropdown).
Lint-friendly: model imports are top-level and uses typing.cast to
silence false-positive attribute checks on Django model managers.
"""

from typing import Any, Dict, cast

from .models import Notification, Category


def notifications(request) -> Dict[str, Any]:
    """Provide unread notification count and latest notifications.

    Added to templates so the navbar can display an unread badge and a
    short dropdown of recent notifications for the current user.
    """
    user = getattr(request, 'user', None)
    if not user or not user.is_authenticated:
        return {
            'unread_notifications_count': 0,
            'recent_notifications': [],
        }

    # Cast Notification to Any so linters/mypy don't complain about the
    # Django model manager (objects) being dynamically provided.
    NotificationAny = cast(Any, Notification)

    # Pylint may report ``no-member`` for dynamically-created Django model
    # managers (objects). Silence with a trailing pylint-disable on the
    # completed expression while keeping mypy's attr-defined ignore.
    # pylint: disable=no-member
    unread_qs = NotificationAny.objects.filter(  # type: ignore[attr-defined]
        recipient=user, is_read=False
    )  # pylint: disable=no-member
    # pylint: disable=E1101
    unread_count = unread_qs.count()

    recent_qs = NotificationAny.objects.filter(  # type: ignore[attr-defined]
        recipient=user
    )  # pylint: disable=no-member
    recent_qs = recent_qs.order_by('-created_at')[:5]  # pylint: disable=E1101
    recent = list(recent_qs)

    return {
        'unread_notifications_count': unread_count,
        'recent_notifications': recent,
    }


def categories(_request) -> Dict[str, Any]:
    """Provide active categories for navigation."""
    # '_request' argument is required by Django context processors,
    #  even if unused
    CategoryAny = cast(Any, Category)
    # Get active categories ordered by their order field
    # pylint: disable=no-member
    active_categories = list(
        CategoryAny.objects.filter(  # type: ignore[attr-defined]
            is_active=True
        ).order_by('order')  # pylint: disable=E1101
    )
    return {
        'navigation_categories': active_categories,
    }
