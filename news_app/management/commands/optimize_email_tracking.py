"""
Management command to optimize email tracking performance.

This command adds database indexes and performs cleanup operations
to ensure optimal performance for email tracking features.
"""

from django.core.management.base import BaseCommand
from django.db import connection, transaction
from django.utils import timezone
from datetime import timedelta
from news_app.models import Notification
import logging

logger = logging.getLogger(__name__)


class Command(BaseCommand):
    """Management command for email tracking optimization."""
    
    help = 'Optimize email tracking performance with indexes and cleanup'
    
    def add_arguments(self, parser):
        """Add command line arguments."""
        parser.add_argument(
            '--cleanup-days',
            type=int,
            default=90,
            help='Clean up notifications older than N days (default: 90)'
        )
        parser.add_argument(
            '--dry-run',
            action='store_true',
            help='Show what would be done without making changes'
        )
        parser.add_argument(
            '--skip-indexes',
            action='store_true',
            help='Skip creating database indexes'
        )
    
    def handle(self, *args, **options):
        """Execute the optimization command."""
        self.stdout.write(
            self.style.SUCCESS('Starting email tracking optimization...')
        )
        
        dry_run = options['dry_run']
        cleanup_days = options['cleanup_days']
        skip_indexes = options['skip_indexes']
        
        if dry_run:
            self.stdout.write(
                self.style.WARNING('DRY RUN MODE - No changes will be made')
            )
        
        # Create database indexes for performance
        if not skip_indexes:
            self._create_indexes(dry_run)
        
        # Clean up old notifications
        self._cleanup_old_notifications(cleanup_days, dry_run)
        
        # Update statistics
        self._update_statistics()
        
        self.stdout.write(
            self.style.SUCCESS('Email tracking optimization completed!')
        )
    
    def _create_indexes(self, dry_run):
        """Create database indexes for email tracking performance."""
        self.stdout.write('Creating database indexes...')
        
        indexes = [
            {
                'name': 'idx_notification_read_token',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_notification_read_token ON news_app_notification (read_token);',
                'description': 'Index on read_token for email tracking'
            },
            {
                'name': 'idx_notification_is_read_created',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_notification_is_read_created ON news_app_notification (is_read, created_at);',
                'description': 'Composite index on is_read and created_at'
            },
            {
                'name': 'idx_notification_recipient_created',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_notification_recipient_created ON news_app_notification (recipient_id, created_at);',
                'description': 'Index for recipient notifications'
            },
            {
                'name': 'idx_notification_email_opened_at',
                'sql': 'CREATE INDEX IF NOT EXISTS idx_notification_email_opened_at ON news_app_notification (email_opened_at);',
                'description': 'Index on email_opened_at for analytics'
            }
        ]
        
        if dry_run:
            for index in indexes:
                self.stdout.write(f"  Would create: {index['description']}")
            return
        
        with connection.cursor() as cursor:
            for index in indexes:
                try:
                    cursor.execute(index['sql'])
                    self.stdout.write(
                        self.style.SUCCESS(
                            f"  ✓ Created: {index['description']}"
                        )
                    )
                except Exception as e:
                    self.stdout.write(
                        self.style.ERROR(
                            f"  ✗ Failed to create {index['name']}: {e}"
                        )
                    )
    
    def _cleanup_old_notifications(self, cleanup_days, dry_run):
        """Clean up old read notifications."""
        self.stdout.write(
            f'Cleaning up notifications older than {cleanup_days} days...'
        )
        
        cutoff_date = timezone.now() - timedelta(days=cleanup_days)
        
        # Count notifications to be cleaned
        old_notifications = Notification.objects.filter(
            is_read=True,
            email_opened_at__lt=cutoff_date
        )
        count = old_notifications.count()
        
        if count == 0:
            self.stdout.write('  No notifications to clean up.')
            return
        
        if dry_run:
            self.stdout.write(
                f"  Would delete {count} old read notifications"
            )
            return
        
        # Delete in batches to avoid locking
        batch_size = 1000
        deleted_total = 0
        
        while True:
            with transaction.atomic():
                batch_ids = list(
                    old_notifications.values_list('id', flat=True)[:batch_size]
                )
                if not batch_ids:
                    break
                
                deleted_count = Notification.objects.filter(
                    id__in=batch_ids
                ).delete()[0]
                deleted_total += deleted_count
                
                self.stdout.write(
                    f"  Deleted batch: {deleted_count} notifications "
                    f"(Total: {deleted_total})"
                )
        
        self.stdout.write(
            self.style.SUCCESS(
                f"  ✓ Cleaned up {deleted_total} old notifications"
            )
        )
    
    def _update_statistics(self):
        """Display current notification statistics."""
        self.stdout.write('Current notification statistics:')
        
        total_notifications = Notification.objects.count()
        read_notifications = Notification.objects.filter(is_read=True).count()
        unread_notifications = total_notifications - read_notifications
        
        # Email tracking statistics
        email_tracked = Notification.objects.filter(
            email_opened_at__isnull=False
        ).count()
        
        recent_notifications = Notification.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        ).count()
        
        self.stdout.write(f"  Total notifications: {total_notifications}")
        self.stdout.write(f"  Read notifications: {read_notifications}")
        self.stdout.write(f"  Unread notifications: {unread_notifications}")
        self.stdout.write(f"  Email tracked: {email_tracked}")
        self.stdout.write(f"  Last 7 days: {recent_notifications}")
        
        if total_notifications > 0:
            read_percentage = (read_notifications / total_notifications) * 100
            track_percentage = (email_tracked / total_notifications) * 100
            
            self.stdout.write(
                f"  Read rate: {read_percentage:.1f}%"
            )
            self.stdout.write(
                f"  Email tracking rate: {track_percentage:.1f}%"
            )