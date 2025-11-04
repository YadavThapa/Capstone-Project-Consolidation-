"""Background tasks for news_app.

This module defines Celery tasks. Importing Celery is optional; the
signal handler will fall back to synchronous sending if Celery is not
available or configured in the environment.
"""
import logging
from typing import Any, Optional

from django.conf import settings

# Editor/static analysis: these checks often misreport for Django projects
# where models and optional packages (Celery) are resolved at runtime.
# Disable noisy checks locally for this helper module.
# pylint: disable=import-error,no-member,import-outside-toplevel,broad-except
# pylint: disable=invalid-name

try:
    from celery import shared_task  # type: ignore
except Exception:  # pragma: no cover - Celery not installed in some envs
    shared_task = None  # type: ignore

logger = logging.getLogger(__name__)


if shared_task is not None:
    @shared_task(bind=False)
    def send_article_emails_task(article_id: int) -> bool:
        """Celery task to send article emails to subscribers.

        Returns True on success, False on failure. The task is defensive and
        logs errors rather than raising to avoid task-level crashes.
        """
        try:
            # Import inside task to avoid circular imports at module load
            from .models import Article, Notification  # type: ignore
            from django.core.mail import send_mass_mail

            article = Article.objects.get(id=article_id)
            subscribers_by_type = article.get_subscribers_by_type()

            if not subscribers_by_type['all']:
                return True

            # Get author display name
            author_any: Optional[Any] = getattr(article, 'author', None)
            author_name = ''
            if author_any is not None:
                get_full = getattr(author_any, 'get_full_name', None)
                if callable(get_full):
                    try:
                        author_name = get_full()
                    except Exception:
                        author_name = getattr(author_any, 'username', '')
                else:
                    author_name = getattr(author_any, 'username', '')

            messages = []
            notif_objs = []

            # Handle publisher subscribers
            if subscribers_by_type['publisher']:
                for subscriber in subscribers_by_type['publisher']:
                    if not getattr(subscriber, 'email', None):
                        continue

                    subject = (f'New Article from {article.publisher.name}: '
                               f'{article.title}')
                    message = (
                        f'A new article has been published by '
                        f'{article.publisher.name}!\n\n'
                        f'Title: {article.title}\n'
                        f'Author: {author_name}\n'
                        f'Publisher: {article.publisher.name}\n\n'
                        f'{article.summary}\n\n'
                        f'Read more: [Your site]/articles/{article.slug}/\n\n'
                        f'You subscribed to {article.publisher.name}.'
                    )

                    from_email = getattr(settings, 'DEFAULT_FROM_EMAIL',
                                         settings.EMAIL_HOST_USER)
                    messages.append((
                        subject, message, from_email,
                        [subscriber.email]
                    ))
                    notif_objs.append(Notification(
                        recipient=subscriber,
                        article=article,
                        title=subject,
                        message=message,
                        notification_type='publisher'
                    ))

            # Handle journalist subscribers
            for subscriber in subscribers_by_type['journalist']:
                if not getattr(subscriber, 'email', None):
                    continue

                # Skip if already notified as publisher subscriber
                if (subscribers_by_type['publisher'] and
                        subscriber in subscribers_by_type['publisher']):
                    continue

                subject = f'New Article by {author_name}: {article.title}'
                publisher_name = (article.publisher.name if article.publisher
                                  else "Independent")
                message = (
                    f'A new article has been published by journalist '
                    f'{author_name}!\n\n'
                    f'Title: {article.title}\n'
                    f'Author: {author_name}\n'
                    f'Publisher: {publisher_name}\n\n'
                    f'{article.summary}\n\n'
                    f'Read more: [Your website]/articles/{article.slug}/\n\n'
                    f'You subscribed to {author_name}.'
                )

                from_email = getattr(settings, 'DEFAULT_FROM_EMAIL',
                                     settings.EMAIL_HOST_USER)
                messages.append((
                    subject, message, from_email,
                    [subscriber.email]
                ))
                notif_objs.append(Notification(
                    recipient=subscriber,
                    article=article,
                    title=subject,
                    message=message,
                    notification_type='journalist'
                ))

            # Create notifications in database
            if notif_objs:
                Notification.objects.bulk_create(notif_objs)

            # Send emails
            if messages:
                try:
                    send_mass_mail(messages, fail_silently=False)
                except Exception as exc:  # pragma: no cover - log and continue
                    logger.exception('SMTPException in Celery task: %s', exc)

            return True
        except Exception as exc:  # pragma: no cover - task-level catch-all
            logger.exception('Error in send_article_emails_task: %s', exc)
            return False
