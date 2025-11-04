"""Signal handlers for article approval notifications.

When an Article is approved, this module sends notification emails to
subscribers and optionally posts the article to X (formerly Twitter).
Handlers are defensive to avoid raising exceptions during request
processing or management tasks.
"""

from typing import Any, cast, Optional
import logging
import smtplib

import requests

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.core.mail import send_mass_mail
from django.conf import settings
from django.utils import timezone

from .models import Article, Notification

# Pylint: these editor checks can be noisy for Django runtime imports and
# defensive signal handlers. Keep the disables local to this module.
# pylint: disable=import-error,no-name-in-module
# pylint: disable=import-outside-toplevel,broad-except

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Article)
def article_approved_handler(  # pylint: disable=unused-argument
    sender: Any, instance: Article, created: bool, **kwargs: Any
) -> None:
    """Handle article approval to notify subscribers and post to X.

    This handler is defensive: it checks approval timestamps to avoid
    duplicate sends and logs failures instead of raising.
    """
    # Only trigger when article is approved and has 'approved' status
    if not (instance.is_approved and instance.status == 'approved'):
        return

    # If approved_at exists, avoid duplicate sends within a short window
    if instance.approved_at:
        time_since_approval = timezone.now() - instance.approved_at
        if time_since_approval.total_seconds() > 10:
            return

    # Send emails and post to X. Each helper handles its own expected
    # error types and logs them. Prefer sending emails asynchronously
    # with Celery when available; fall back to synchronous sending.
    send_article_emails(instance)
    post_to_x(instance)


def _send_article_emails_sync(article: Article) -> None:
    """Synchronous fallback to send article emails to subscribers.

    The Celery task performs the same work; this helper is used when
    Celery isn't available or as a fallback during errors.
    """
    subscribers_by_type = article.get_subscribers_by_type()

    if not subscribers_by_type['all']:
        return

    # Cast author to Any for linters/static checkers; Django user model
    # provides these attributes at runtime.
    author_any = cast(Any, article.author)
    author_display = author_any.get_full_name() or author_any.username

    # Prepare email messages for all subscribers
    messages = []
    notif_objs = []

    # Create notifications first to get read tokens
    # Handle publisher subscribers
    if subscribers_by_type['publisher']:
        for subscriber in subscribers_by_type['publisher']:
            if not subscriber.email:
                continue

            subject = (f'New Article from {article.publisher.name}: '
                       f'{article.title}')

            # Create notification first to get read_token
            notification = Notification(
                recipient=subscriber,
                article=article,
                title=subject,
                message='',  # Will be updated with tracking
                notification_type='publisher'
            )
            notification.save()  # This generates read_token

            # Create message with tracking pixel
            base_url = getattr(settings, 'BASE_URL', 'http://127.0.0.1:8000')
            tracking_url = (
                f'{base_url}/track-email/{notification.read_token}/'
            )

            # Create HTML email content with tracking pixel
            mark_read_url = (
                f'{base_url}/mark-read/{notification.pk}/'
            )
            article_url = (
                f'{base_url}/articles/{article.slug}/'
            )
            publisher_name = (
                article.publisher.name if article.publisher else "Independent"
            )

            html_message = f'''
            <!DOCTYPE html>
            <html lang="en">
            <head>
                <meta charset="UTF-8">
                <meta name="viewport" content="width=device-width,
                initial-scale=1.0">
                <title>New Article from {publisher_name}</title>
                <style>
                    body {{
                        font-family: 'Segoe UI', Tahoma, Geneva,
                         Verdana, sans-serif;
                        line-height: 1.6;
                        color: #333;
                        max-width: 600px;
                        margin: 0 auto;
                        padding: 20px;
                        background-color: #f8f9fa;
                    }}
                    .email-container {{
                        background-color: white;
                        border-radius: 8px;
                        padding: 30px;
                        box-shadow: 0 2px 10px rgba(0,0,0,0.1);
                    }}
                    .header {{
                        border-bottom: 3px solid #007bff;
                        padding-bottom: 20px;
                        margin-bottom: 25px;
                    }}
                    .publisher-name {{
                        color: #007bff;
                        font-weight: bold;
                        font-size: 1.1em;
                    }}
                    .article-title {{
                        font-size: 1.5em;
                        font-weight: bold;
                        color: #2c3e50;
                        margin: 15px 0;
                    }}
                    .article-meta {{
                        color: #666;
                        font-size: 0.9em;
                        margin-bottom: 20px;
                    }}
                    .article-summary {{
                        background-color: #f8f9fa;
                        padding: 15px;
                        border-left: 4px solid #007bff;
                        margin: 20px 0;
                        font-style: italic;
                    }}
                    .cta-button {{
                        display: inline-block;
                        background: linear-gradient(135deg, #007bff, #0056b3);
                        color: white !important;
                        padding: 15px 30px;
                        text-decoration: none;
                        border-radius: 25px;
                        font-weight: bold;
                        margin: 20px 0;
                        transition: all 0.3s ease;
                        box-shadow: 0 4px 15px rgba(0,123,255,0.3);
                    }}
                    .cta-button:hover {{
                        transform: translateY(-2px);
                        box-shadow: 0 6px 20px rgba(0,123,255,0.4);
                    }}
                    .subscription-info {{
                        background-color: #e9ecef;
                        padding: 10px;
                        border-radius: 5px;
                        margin-top: 25px;
                        font-size: 0.9em;
                        color: #666;
                    }}
                    .footer {{
                        margin-top: 30px;
                        padding-top: 20px;
                        border-top: 1px solid #dee2e6;
                        font-size: 0.8em;
                        color: #999;
                    }}
                    .footer a {{
                        color: #007bff;
                        text-decoration: none;
                    }}
                    .read-button {{
                        display: inline-block;
                        background-color: #28a745;
                        color: white !important;
                        padding: 8px 16px;
                        text-decoration: none;
                        border-radius: 15px;
                        font-size: 0.8em;
                        margin-right: 10px;
                    }}
                </style>
            </head>
            <body>
                <div class="email-container">
                    <div class="header">
                        <div class="publisher-name">📰 {publisher_name}</div>
                        <div class="article-title">{article.title}</div>
                        <div class="article-meta">
                            By <strong>{author_display}</strong> •
                             Just published
                        </div>
                    </div>

                    <div class="article-summary">
                        {article.summary}
                    </div>

                    <div style="text-align: center; margin: 30px 0;">
                        <a href="{article_url}" class="cta-button">
                            📖 Read Full Article Now
                        </a>
                    </div>

                    <div class="subscription-info">
                        <strong>✅ You're subscribed to:</strong>
                         {publisher_name}<br>
                        Stay informed with the latest news and articles
                        from your favorite publishers.
                    </div>

                    <div class="footer">
                        <a href="{mark_read_url}" class="read-button">
                        ✓ Mark as Read</a>
                        <span style="color: #ccc;">|</span>
                        <small>Email tracking enabled •
                        News Application</small>
                    </div>
                </div>

                <!-- Tracking pixel -->
                <img src="{tracking_url}" width="1" height="1"
                 style="display:none;" alt="" />
            </body>
            </html>
            '''

            message = (
                f'📰 New Article from {publisher_name}!\n\n'
                f'Title: {article.title}\n'
                f'Author: {author_display}\n'
                f'Publisher: {publisher_name}\n\n'
                f'{article.summary}\n\n'
                f'Read the full article: {article_url}\n\n'
                f'✅ You subscribed to {publisher_name}\n\n'
                f'---\n'
                f'Mark as read: {mark_read_url}\n'
                f'This email includes read tracking for your convenience.'
            )

            # Update notification with final message
            notification.message = message
            notification.save()

            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL',
                                 settings.EMAIL_HOST_USER)
            messages.append((
                subject, message, from_email, [subscriber.email]
            ))

            # Send HTML email separately for better tracking
            try:
                from django.core.mail import EmailMultiAlternatives
                email = EmailMultiAlternatives(
                    subject, message, from_email, [subscriber.email]
                )
                email.attach_alternative(html_message, "text/html")
                email.send()
            except Exception as e:
                logger.warning("Failed to send HTML email: %s", e)
            notif_objs.append(notification)

    # Handle journalist subscribers
    for subscriber in subscribers_by_type['journalist']:
        if not subscriber.email:
            continue

        # Skip if already notified as publisher subscriber
        if (subscribers_by_type['publisher'] and
                subscriber in subscribers_by_type['publisher']):
            continue

        subject = f'New Article by {author_display}: {article.title}'
        publisher_name = (article.publisher.name if article.publisher
                          else "Independent")
        message = (
            f'A new article has been published by journalist '
            f'{author_display}!\n\n'
            f'Title: {article.title}\n'
            f'Author: {author_display}\n'
            f'Publisher: {publisher_name}\n\n'
            f'{article.summary}\n\n'
            f'Read more: [Your website]/articles/{article.slug}/\n\n'
            f'You subscribed to {author_display}.'
        )

        # Create notification first to get read_token
        notification = Notification(
            recipient=subscriber,
            article=article,
            title=subject,
            message='',  # Will be updated with tracking
            notification_type='journalist'
        )
        notification.save()  # This generates read_token

        # Add tracking to message
        base_url = getattr(settings, 'BASE_URL', 'http://127.0.0.1:8000')
        tracking_url = f'{base_url}/track-email/{notification.read_token}/'
        mark_read_url = (
            f'{base_url}/mark-read/{notification.id}/'
        )
        article_url = (
            f'{base_url}/articles/{article.slug}/'
        )

    # Create HTML email for journalist subscription
    html_message = (
        f'''
    <!DOCTYPE html>
    <html lang="en">
    <head>
        <meta charset="UTF-8">
        <meta name="viewport" content="width=device-width, initial-scale=1.0">
        <title>New Article by {author_display}</title>
        <style>
            body {{
                font-family: 'Segoe UI', Tahoma, Geneva, Verdana, sans-serif;
                line-height: 1.6;
                color: #333;
                max-width: 600px;
                margin: 0 auto;
                padding: 20px;
                background-color: #f8f9fa;
            }}
            .email-container {{
                background-color: white;
                border-radius: 8px;
                padding: 30px;
                box-shadow: 0 2px 10px rgba(0,0,0,0.1);
            }}
            .header {{
                border-bottom: 3px solid #28a745;
                padding-bottom: 20px;
                margin-bottom: 25px;
            }}
            .journalist-name {{
                color: #28a745;
                font-weight: bold;
                font-size: 1.1em;
            }}
            .article-title {{
                font-size: 1.5em;
                font-weight: bold;
                color: #2c3e50;
                margin: 15px 0;
            }}
            .article-meta {{
                color: #666;
                font-size: 0.9em;
                margin-bottom: 20px;
            }}
            .article-summary {{
                background-color: #f8f9fa;
                padding: 15px;
                border-left: 4px solid #28a745;
                margin: 20px 0;
                font-style: italic;
            }}
            .cta-button {{
                display: inline-block;
                background: linear-gradient(135deg, #28a745, #1e7e34);
                color: white !important;
                padding: 15px 30px;
                text-decoration: none;
                border-radius: 25px;
                font-weight: bold;
                margin: 20px 0;
                transition: all 0.3s ease;
                box-shadow: 0 4px 15px rgba(40,167,69,0.3);
            }}
            .subscription-info {{
                background-color: #d4edda;
                padding: 10px;
                border-radius: 5px;
                margin-top: 25px;
                font-size: 0.9em;
                color: #155724;
            }}
            .footer {{
                margin-top: 30px;
                padding-top: 20px;
                border-top: 1px solid #dee2e6;
                font-size: 0.8em;
                color: #999;
            }}
            .footer a {{
                color: #28a745;
                text-decoration: none;
            }}
            .read-button {{
                display: inline-block;
                background-color: #17a2b8;
                color: white !important;
                padding: 8px 16px;
                text-decoration: none;
                border-radius: 15px;
                font-size: 0.8em;
                margin-right: 10px;
            }}
        </style>
    </head>
    <body>
        <div class="email-container">
            <div class="header">
                <div class="journalist-name">✍️ {author_display}</div>
                <div class="article-title">{article.title}</div>
                <div class="article-meta">
                    Published by <strong>{publisher_name}</strong> • Just now
                </div>
            </div>

            <div class="article-summary">
                {article.summary}
            </div>

            <div style="text-align: center; margin: 30px 0;">
                <a href="{article_url}" class="cta-button">
                    📖 Read {author_display}'s Article
                </a>
            </div>

            <div class="subscription-info">
                <strong>✅ Following journalist:</strong> {author_display}<br>
                Get notified whenever {author_display} publishes new articles.
            </div>

            <div class="footer">
                <a href="{mark_read_url}" class="read-button">
                ✓ Mark as Read</a>
                <span style="color: #ccc;">|</span>
                <small>Email tracking enabled • News Application</small>
            </div>
        </div>

        <!-- Tracking pixel -->
        <img src="{tracking_url}" width="1" height="1"
         style="display:none;" alt="" />
    </body>
    </html>
    '''
    )

    message = (
        f'✍️ New Article by {author_display}!\n\n'
        f'Title: {article.title}\n'
        f'Author: {author_display}\n'
        f'Publisher: {publisher_name}\n\n'
        f'{article.summary}\n\n'
        f'Read the full article: {article_url}\n\n'
        f'✅ You are following {author_display}\n\n'
        f'---\n'
        f'Mark as read: {mark_read_url}\n'
        f'This email includes read tracking for your convenience.'
    )

    # Update notification with final message
    notification.message = message
    notification.save()

    from_email = getattr(
        settings, 'DEFAULT_FROM_EMAIL', settings.EMAIL_HOST_USER
    )
    messages.append(
        (subject, message, from_email, [subscriber.email])
    )

    # Send HTML email separately for better tracking
    try:
        from django.core.mail import EmailMultiAlternatives
        email = EmailMultiAlternatives(
            subject, message, from_email, [subscriber.email]
        )
        email.attach_alternative(html_message, "text/html")
        email.send()
    except Exception as e:
        logger.warning("Failed to send HTML email: %s", e)

    notif_objs.append(notification)

    # Notifications already created individually with read tokens
    # Log the count
    logger.info('Created %d notifications with read tracking', len(notif_objs))

    # Send emails
    if messages:
        try:
            send_mass_mail(messages, fail_silently=False)
            pub_count = (len(subscribers_by_type['publisher'])
                         if subscribers_by_type['publisher'] else 0)
            jour_count = len(subscribers_by_type['journalist'])
            logger.info('Emails sent for article: %s (Pub: %d, Jour: %d)',
                        article.title, pub_count, jour_count)
        except smtplib.SMTPException as exc:  # pragma: no cover - defensive
            logger.exception('SMTPException sending emails: %s', exc)
        except Exception as exc:  # pragma: no cover - defensive
            # Broad-except as last-resort in signal handling; log it.
            logger.exception('Unexpected error sending emails: %s', exc)


def send_article_emails(article: Article) -> None:
    """Dispatch email sending via Celery when available, else sync."""
    try:
        # Import task lazily so Celery is optional for environments that
        # don't have it installed/configured.
        from .tasks import send_article_emails_task  # type: ignore

        # If the task is defined (Celery available), call it asynchronously.
        if send_article_emails_task is not None:
            try:
                # Use getattr to avoid static-analysis errors when the model
                # stubs don't expose `id`/`pk` attributes.
                article_id: Optional[int] = getattr(article, 'id', None)
                if article_id is not None:
                    # type: ignore[attr-defined]
                    send_article_emails_task.delay(article_id)
                    logger.info(
                        'Dispatched send_article_emails_task for article %s',
                        article_id,
                    )
                    return
            except Exception as exc:  # pragma: no cover - fallback on failure
                logger.exception('Failed to dispatch Celery task: %s', exc)
                # fall through to synchronous sending
    except Exception:
        # Celery not available or import failed — fall back to sync.
        pass

    # Synchronous fallback
    _send_article_emails_sync(article)


def post_to_x(article: Article) -> None:
    """Post article to X (Twitter) using API.

    Uses a short timeout on network calls to avoid hanging the process.
    """
    # Skip posting if X API keys are not configured to avoid failures
    if not getattr(settings, 'X_API_KEY', None):
        return

    # X API v2 endpoint
    url = 'https://api.twitter.com/2/tweets'

    # Prepare tweet content
    author_any = cast(Any, article.author)
    tweet_text = (
        f"{article.title}\n\nBy {author_any.username}\n\n"
        f"{article.summary[:200]}..."
    )

    headers = {
        'Authorization': f'Bearer {settings.X_API_KEY}',
        'Content-Type': 'application/json',
    }

    payload = {'text': tweet_text[:280]}

    # Use a short timeout to prevent hangs
    try:
        response = requests.post(
            url, json=payload, headers=headers, timeout=5
        )
        if response.status_code == 201:
            logger.info('Successfully posted to X: %s', article.title)
        else:
            logger.warning(
                'Error posting to X: %s - %s',
                response.status_code,
                response.text,
            )
    except requests.RequestException as exc:  # network-related exceptions
        logger.exception('RequestException posting to X: %s', exc)


def post_to_facebook(article: Article) -> None:
    """Post article to Facebook using Graph API when configured.

    Requires settings.FACEBOOK_PAGE_ID and settings.FACEBOOK_ACCESS_TOKEN
    to be set. This helper is defensive and logs any failures instead of
    raising so it is safe to call from views or signal handlers.
    """
    page_id = getattr(settings, 'FACEBOOK_PAGE_ID', '')
    token = getattr(settings, 'FACEBOOK_ACCESS_TOKEN', '')

    if not page_id or not token:
        # Not configured — skip posting.
        return

    url = f'https://graph.facebook.com/{page_id}/feed'

    # Build a brief message with title and summary (trimmed)
    author_any = cast(Any, article.author)
    message = (
        f"{article.title}\n\n"
        f"By {author_any.get_full_name() or author_any.username}\n\n"
        f"{(article.summary or '')[:300]}\n\n"
        f"Read: [Your site]/articles/{article.slug}/"
    )

    payload = {
        'message': message,
        'access_token': token,
    }

    try:
        resp = requests.post(url, data=payload, timeout=5)
        if resp.status_code in (200, 201):
            logger.info('Posted article to Facebook: %s', article.title)
        else:
            logger.warning(
                'Facebook post returned %s: %s', resp.status_code, resp.text
            )
    except requests.RequestException as exc:
        logger.exception('RequestException posting to Facebook: %s', exc)
