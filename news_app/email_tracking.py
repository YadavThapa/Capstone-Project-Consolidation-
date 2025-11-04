"""
Email tracking views for notification read status

Enhanced with production-ready error handling, logging, and security features.
"""

import logging

from django.http import HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.http import require_GET
from django.views.decorators.cache import never_cache
from django.core.cache import cache
from django.conf import settings
from django.utils import timezone
from .models import Notification  # pylint: disable=relative-beyond-top-level


logger = logging.getLogger(__name__)

# Cache keys for rate limiting and performance
TRACKING_CACHE_PREFIX = 'email_track:'
RATE_LIMIT_PREFIX = 'rate_limit:'

# Fallback transparent pixel data
TRANSPARENT_PIXEL = (
    b'\x47\x49\x46\x38\x39\x61\x01\x00\x01\x00\x80\x00\x00'
    b'\xff\xff\xff\x00\x00\x00\x21\xf9\x04\x01\x00\x00\x00'
    b'\x00\x2c\x00\x00\x00\x00\x01\x00\x01\x00\x00\x02\x02'
    b'\x04\x01\x00\x3b'
)


def _get_client_info(request):
    """Extract client information for security logging."""
    return {
        'ip': request.META.get('REMOTE_ADDR', 'unknown'),
        'user_agent': request.META.get('HTTP_USER_AGENT', 'unknown')[:200],
        'referer': request.META.get('HTTP_REFERER', 'unknown')[:200],
    }


def _is_rate_limited(token, request):
    """Check if the request should be rate limited."""
    client_info = _get_client_info(request)
    cache_key = f"{RATE_LIMIT_PREFIX}{token}:{client_info['ip']}"

    # Allow 10 requests per minute per IP per token
    current_count = cache.get(cache_key, 0)
    if current_count >= 10:
        return True

    cache.set(cache_key, current_count + 1, 60)  # 1 minute timeout
    return False


@csrf_exempt
@require_GET
@never_cache
def track_email_open(request, token):
    """
    Track when an email notification is opened.
    This endpoint is called when the user opens the email (via tracking pixel).

    Enhanced with rate limiting, caching, and comprehensive error handling.
    URL: /track-email/<token>/
    """
    start_time = timezone.now()
    client_info = _get_client_info(request)

    # Token is already validated by URL pattern as UUID
    # Convert UUID object to string for database lookup
    token_str = str(token)

    # Check rate limiting
    if _is_rate_limited(token_str, request):
        logger.warning(
            "Rate limited tracking request: %s from %s",
            token_str, client_info['ip']
        )
        return _return_tracking_pixel()

    # Check cache first for performance
    cache_key = f"{TRACKING_CACHE_PREFIX}{token_str}"
    cached_result = cache.get(cache_key)

    if cached_result:
        logger.debug("Cached tracking pixel served for token: %s", token_str)
        return _return_tracking_pixel()

    try:
        # Find notification by read_token
        try:
            # pylint: disable=no-member
            notification = Notification.objects.get(read_token=token_str)
        except Notification.DoesNotExist:  # pylint: disable=no-member
            logger.warning(
                "Invalid tracking token: %s from %s",
                token_str, client_info['ip']
            )
            # Cache invalid tokens to prevent repeated DB lookups
            cache.set(cache_key, 'invalid', 3600)  # 1 hour cache
            return _return_tracking_pixel()

        # Mark as read if not already
        if not notification.is_read:
            try:
                notification.mark_as_read()
                logger.info(
                    f"Email opened: Notification {notification.id} "
                    f"to {notification.recipient.email} marked as read "
                    f"from {client_info['ip']} "
                    f"UA: {client_info['user_agent'][:50]}..."
                )

                # Cache successful tracking for performance
                cache_timeout = getattr(
                    settings, 'EMAIL_TRACKING_PIXEL_CACHE_SECONDS', 86400
                )
                cache.set(cache_key, 'tracked', cache_timeout)

            except Exception as db_error:
                logger.error(
                    f"Database error marking notification {notification.id} "
                    f"as read: {db_error}"
                )
                # Continue and return pixel anyway
        else:
            logger.debug(
                f"Notification {notification.id} already read, "
                f"serving cached pixel"
            )

        # Track response time for monitoring
        response_time = (timezone.now() - start_time).total_seconds()
        if response_time > 1.0:  # Log slow requests
            logger.warning(
                "Slow tracking response: %.2fs for token %s",
                response_time, token_str
            )

        return _return_tracking_pixel()

    except Exception as e:
        logger.error(
            "Unexpected error in email tracking for token %s: %s",
            token_str, str(e), exc_info=True
        )
        # Always return a pixel, never fail the tracking request
        return _return_tracking_pixel()


def _return_tracking_pixel():
    """Return a cached tracking pixel response."""
    response = HttpResponse(TRANSPARENT_PIXEL, content_type='image/gif')

    # Security headers
    response['Cache-Control'] = 'no-cache, no-store, must-revalidate'
    response['Pragma'] = 'no-cache'
    response['Expires'] = '0'
    response['X-Robots-Tag'] = 'noindex, nofollow, noarchive, nosnippet'

    # CORS headers for email clients
    response['Access-Control-Allow-Origin'] = '*'
    response['Access-Control-Allow-Methods'] = 'GET'

    return response


@csrf_exempt
@require_GET
@never_cache
def mark_notification_read(request, notification_id):
    """
    Manual endpoint to mark notification as read.
    Enhanced with comprehensive error handling and security features.

    URL: /mark-read/<notification_id>/
    """
    start_time = timezone.now()
    client_info = _get_client_info(request)

    # Validate notification_id is numeric
    try:
        notification_id = int(notification_id)
        if notification_id <= 0:
            raise ValueError("Invalid ID")
    except (ValueError, TypeError):
        logger.warning(
            f"Invalid notification ID format: {notification_id} "
            f"from {client_info['ip']}"
        )
        return _render_error_page(
            "Invalid Request",
            "The notification ID format is invalid.",
            400
        )

    # Rate limiting for manual mark as read
    cache_key = f"{RATE_LIMIT_PREFIX}mark_read:{client_info['ip']}"
    current_count = cache.get(cache_key, 0)
    if current_count >= 20:  # 20 requests per minute per IP
        logger.warning(
            f"Rate limited mark-read request from {client_info['ip']}"
        )
        return _render_error_page(
            "Too Many Requests",
            "Please wait a moment before trying again.",
            429
        )
    cache.set(cache_key, current_count + 1, 60)

    try:
        # Find notification
        try:
            # pylint: disable=no-member
            notification = Notification.objects.get(id=notification_id)
        except Notification.DoesNotExist:  # pylint: disable=no-member
            logger.warning(
                f"Notification not found: ID {notification_id} "
                f"from {client_info['ip']}"
            )
            return _render_error_page(
                "Notification Not Found",
                "The requested notification could not be found.",
                404
            )

        # Mark as read
        was_already_read = notification.is_read

        if not was_already_read:
            try:
                notification.mark_as_read()
                logger.info(
                    f"Notification {notification_id} marked as read "
                    f"by manual action from {client_info['ip']}"
                )
                message = "✅ Notification marked as read successfully!"
                message_class = "success"
            except Exception as db_error:
                logger.error(
                    f"Database error marking notification {notification_id} "
                    f"as read: {db_error}",
                    exc_info=True
                )
                return _render_error_page(
                    "Database Error",
                    "Unable to update notification status. Please try again.",
                    500
                )
        else:
            message = "ℹ️ Notification was already marked as read."
            message_class = "info"
            logger.debug(
                f"Notification {notification_id} already read, "
                f"request from {client_info['ip']}"
            )

        # Track response time
        response_time = (timezone.now() - start_time).total_seconds()
        if response_time > 2.0:
            logger.warning(
                f"Slow mark-read response: {response_time:.2f}s for "
                f"notification {notification_id}"
            )

        return _render_success_page(message, notification_id, message_class)

    except Exception as e:
        logger.error(
            f"Unexpected error marking notification {notification_id} "
            f"as read: {e}",
            exc_info=True
        )
        return _render_error_page(
            "Server Error",
            "An unexpected error occurred. Please try again later.",
            500
        )


def _render_success_page(message, notification_id, message_class):
    """Render success page for mark as read."""
    current_timestamp = timezone.now().strftime('%Y-%m-%d %H:%M:%S UTC')
    html_response = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Email Tracking Confirmation</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                text-align: center;
                padding: 50px;
                background: linear-gradient(135deg, #667eea 0%, #764ba2 100%);
                color: white;
                min-height: 100vh;
                margin: 0;
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            .container {{
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border-radius: 15px;
                padding: 40px;
                box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
                border: 1px solid rgba(255, 255, 255, 0.18);
            }}
            .{message_class} {{
                color: {"#4CAF50" if message_class == "success" else
                        "#2196F3"};
                font-size: 24px;
                margin-bottom: 20px;
            }}
            .info {{
                color: rgba(255, 255, 255, 0.8);
                font-size: 16px;
                margin: 10px 0;
            }}
            .close-btn {{
                background: #4CAF50;
                color: white;
                border: none;
                padding: 12px 24px;
                border-radius: 25px;
                cursor: pointer;
                font-size: 16px;
                margin-top: 20px;
                transition: background 0.3s;
            }}
            .close-btn:hover {{
                background: #45a049;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="{message_class}">{message}</h1>
            <p class="info">Notification ID: {notification_id}</p>
            <p class="info">Timestamp: {current_timestamp}</p>
            <button class="close-btn" onclick="window.close();">
                Close Window
            </button>
        </div>
    </body>
    </html>
    """
    return HttpResponse(html_response, content_type='text/html')


def _render_error_page(title, message, status_code):
    """Render error page with proper status code."""
    html_response = f"""
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>Email Tracking - {title}</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                text-align: center;
                padding: 50px;
                background: linear-gradient(135deg, #ff6b6b 0%, #ee5a24 100%);
                color: white;
                min-height: 100vh;
                margin: 0;
                display: flex;
                align-items: center;
                justify-content: center;
            }}
            .container {{
                background: rgba(255, 255, 255, 0.1);
                backdrop-filter: blur(10px);
                border-radius: 15px;
                padding: 40px;
                box-shadow: 0 8px 32px rgba(31, 38, 135, 0.37);
                border: 1px solid rgba(255, 255, 255, 0.18);
            }}
            .error {{
                color: #ffcccb;
                font-size: 24px;
                margin-bottom: 20px;
            }}
            .info {{
                color: rgba(255, 255, 255, 0.8);
                font-size: 16px;
                margin: 10px 0;
            }}
        </style>
    </head>
    <body>
        <div class="container">
            <h1 class="error">{title}</h1>
            <p class="info">{message}</p>
            <p class="info">Status: {status_code}</p>
        </div>
    </body>
    </html>
    """
    return HttpResponse(
        html_response, content_type='text/html', status=status_code
    )
