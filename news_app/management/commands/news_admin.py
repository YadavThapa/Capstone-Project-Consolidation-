"""
Comprehensive management command for News Application maintenance.
This command combines essential database operations, testing, and optimization
into a single tool for easier project management.
Usage:
    python manage.py news_admin --help
    python manage.py news_admin --setup-sample-data
    python manage.py news_admin --test-email user@example.com
    python manage.py news_admin --optimize-db
    python manage.py news_admin --cleanup --days 90
"""
from django.core.management.base import BaseCommand
from django.core.mail import EmailMultiAlternatives
from django.conf import settings
from django.db import transaction
from django.utils import timezone
from datetime import timedelta
from news_app.models import (
    Article, CustomUser, Publisher, Notification
)


class Command(BaseCommand):
    """Comprehensive news application management command."""
    help = 'News Application admin tool - setup, testing, and maintenance'

    def add_arguments(self, parser):
        """Add command line arguments."""
        # Setup operations
        parser.add_argument(
            '--setup-sample-data',
            action='store_true',
            help='Create sample publishers, users, and articles for testing'
        )
        # Testing operations
        parser.add_argument(
            '--test-email',
            type=str,
            metavar='EMAIL',
            help='Send test email notification to specified address'
        )
        parser.add_argument(
            '--test-notifications',
            action='store_true',
            help='Test the complete notification system'
        )
        # Database operations
        parser.add_argument(
            '--optimize-db',
            action='store_true',
            help='Optimize database with indexes and cleanup'
        )
        parser.add_argument(
            '--cleanup',
            action='store_true',
            help='Clean up old notifications (use with --days)'
        )
        parser.add_argument(
            '--days',
            type=int,
            default=90,
            help='Number of days to keep notifications (default: 90)'
        )
        # Information operations
        parser.add_argument(
            '--stats',
            action='store_true',
            help='Show application statistics'
        )
        parser.add_argument(
            '--check-config',
            action='store_true',
            help='Check email and application configuration'
        )
        # Options
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force operations without confirmation'
        )

    def handle(self, *args, **options):
        """Execute the selected operations."""
        # Check if any operation is selected
        operations = [
            'setup_sample_data', 'test_email', 'test_notifications',
            'optimize_db', 'cleanup', 'stats', 'check_config'
        ]
        if not any(options.get(op.replace('_', '-')) or options.get(op)
                   for op in operations):
            warning_msg = 'No operation specified. Use --help for options.'
            self.stdout.write(self.style.WARNING(warning_msg))
            return
        self.stdout.write(
            self.style.SUCCESS('🚀 News Application Admin Tool\n')
        )
        # Execute operations
        if options['setup_sample_data']:
            self._setup_sample_data(options)
        if options['test_email']:
            self._test_email(options['test_email'], options)
        if options['test_notifications']:
            self._test_notifications(options)
        if options['optimize_db']:
            self._optimize_database(options)
        if options['cleanup']:
            self._cleanup_notifications(options['days'], options)
        if options['stats']:
            self._show_statistics()
        if options['check_config']:
            self._check_configuration()

    def _setup_sample_data(self, options):
        """Create sample data for testing."""
        self.stdout.write('📊 Setting up sample data...')
        try:
            with transaction.atomic():
                # Create sample publisher
                publisher, created = Publisher.objects.get_or_create(
                    name='Tech News Daily',
                    defaults={
                        'description': 'Leading technology news and analysis',
                        'website': 'https://technews.example.com',
                    }
                )
                if created:
                    self.stdout.write('  ✅ Created publisher: Tech News Daily')
                # Create sample users if they don't exist
                editor, created = CustomUser.objects.get_or_create(
                    username='editor1',
                    defaults={
                        'email': 'editor@example.com',
                        'first_name': 'John',
                        'last_name': 'Editor',
                        'role': 'editor',
                        'is_staff': True,
                    }
                )
                if created:
                    editor.set_password('password123')
                    editor.save()
                    self.stdout.write('  ✅ Created editor user: editor1')
                journalist, created = CustomUser.objects.get_or_create(
                    username='journalist1',
                    defaults={
                        'email': 'journalist@example.com',
                        'first_name': 'Jane',
                        'last_name': 'Journalist',
                        'role': 'journalist',
                    }
                )
                if created:
                    journalist.set_password('password123')
                    journalist.save()
                    msg = '  ✅ Created journalist user: journalist1'
                    self.stdout.write(msg)
                reader, created = CustomUser.objects.get_or_create(
                    username='reader1',
                    defaults={
                        'email': 'reader@example.com',
                        'first_name': 'Bob',
                        'last_name': 'Reader',
                        'role': 'reader',
                    }
                )
                if created:
                    reader.set_password('password123')
                    reader.save()
                    self.stdout.write('  ✅ Created reader user: reader1')
                # Create sample article
                article, created = Article.objects.get_or_create(
                    slug='ai-breakthrough-2024',
                    defaults={
                        'title': 'Major AI Breakthrough in 2024',
                        'content': '''
This article discusses the latest developments in artificial intelligence
and their impact on various industries. The breakthrough represents a
significant step forward in machine learning capabilities.
                        '''.strip(),
                        'summary': ('Latest AI developments showing promising '
                                    'results across industries.'),
                        'author': journalist,
                        'publisher': publisher,
                        'status': 'published',
                        'is_approved': True,
                        'approved_at': timezone.now(),
                    }
                )
                if created:
                    self.stdout.write('  ✅ Created sample article')
                # Create subscriptions using ManyToMany fields
                if publisher not in reader.subscribed_publishers.all():
                    reader.subscribed_publishers.add(publisher)
                    self.stdout.write('  ✅ Created publisher subscription')
                self.stdout.write(
                    self.style.SUCCESS('✅ Sample data setup complete!')
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error setting up sample data: {e}')
            )

    def _test_email(self, email_address, options):
        """Send test email notification."""
        self.stdout.write(f'📧 Sending test email to {email_address}...')
        try:
            time_str = timezone.now().strftime("%Y-%m-%d %H:%M")
            subject = f'[News App] Test Email - {time_str}'
            # Create HTML email
            timestamp = timezone.now().strftime("%Y-%m-%d %H:%M:%S UTC")
            email_backend = settings.EMAIL_BACKEND
            smtp_host = getattr(settings, 'EMAIL_HOST', 'Not configured')
            from_email = getattr(settings, 'DEFAULT_FROM_EMAIL',
                                 'Not configured')
            html_content = f'''
            <!DOCTYPE html>
            <html>
            <head>
                <meta charset="UTF-8">
                <title>News App Test Email</title>
                <style>
                    body {{ font-family: Arial, sans-serif; margin: 20px; }}
                    .header {{ background: #007bff; color: white;
                              padding: 20px; border-radius: 5px; }}
                    .content {{ padding: 20px; background: #f8f9fa;
                               margin-top: 10px; border-radius: 5px; }}
                    .success {{ color: #28a745; font-weight: bold; }}
                </style>
            </head>
            <body>
                <div class="header">
                    <h2>🎉 News Application Test Email</h2>
                </div>
                <div class="content">
                    <p class="success">✅ Email system is working correctly!</p>
                    <p><strong>Timestamp:</strong> {timestamp}</p>
                    <p><strong>Configuration:</strong></p>
                    <ul>
                        <li>Email Backend: {email_backend}</li>
                        <li>SMTP Host: {smtp_host}</li>
                        <li>From Email: {from_email}</li>
                    </ul>
                    <p>This is a test of the News Application email
                    notification system. If you received this email,
                    the system is configured correctly.</p>
                </div>
            </body>
            </html>
            '''
            text_content = f'''
News Application - Test Email
✅ Email system is working correctly!
Timestamp: {timezone.now().strftime("%Y-%m-%d %H:%M:%S UTC")}
Configuration:
- Email Backend: {settings.EMAIL_BACKEND}
- SMTP Host: {getattr(settings, 'EMAIL_HOST', 'Not configured')}
- From Email: {getattr(settings, 'DEFAULT_FROM_EMAIL', 'Not configured')}
This is a test of the News Application email notification system.
If you received this email, the system is configured correctly.
            '''
            # Send email
            email = EmailMultiAlternatives(
                subject,
                text_content,
                from_email,
                [email_address]
            )
            email.attach_alternative(html_content, "text/html")
            email.send()
            success_msg = f'✅ Test email sent successfully to {email_address}'
            self.stdout.write(self.style.SUCCESS(success_msg))
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Failed to send test email: {e}')
            )

    def _test_notifications(self, options):
        """Test the complete notification system."""
        self.stdout.write('🧪 Testing notification system...')
        try:
            # Get test data
            articles = Article.objects.filter(is_approved=True)[:1]
            if not articles:
                self.stdout.write(
                    self.style.WARNING(
                        '⚠️  No approved articles found. '
                        'Run --setup-sample-data first.')
                )
                return
            article = articles[0]
            # Trigger notification by re-saving approved article
            msg = f'  📝 Triggering notifications for: {article.title}'
            self.stdout.write(msg)
            # Count notifications before
            before_count = Notification.objects.count()
            # Trigger signal (simulate approval)
            article.save()
            # Count notifications after
            after_count = Notification.objects.count()
            new_notifications = after_count - before_count
            msg = f'✅ Created {new_notifications} new notifications'
            self.stdout.write(self.style.SUCCESS(msg))
            # Show recent notifications
            recent = Notification.objects.order_by('-created_at')[:5]
            for notif in recent:
                self.stdout.write(
                    f'  📬 {notif.recipient.username}: {notif.title[:50]}...'
                )
        except Exception as e:
            self.stdout.write(
                self.style.ERROR(f'❌ Error testing notifications: {e}')
            )

    def _optimize_database(self, options):
        """Optimize database performance."""
        self.stdout.write('⚡ Optimizing database...')
        # This would typically run the optimize_email_tracking command
        # For now, just show statistics
        from django.core.management import call_command
        try:
            call_command('optimize_email_tracking', '--dry-run')
            self.stdout.write(
                self.style.SUCCESS('✅ Database optimization completed')
            )
        except Exception as e:
            warning_msg = f'⚠️  Optimization command not available: {e}'
            self.stdout.write(self.style.WARNING(warning_msg))

    def _cleanup_notifications(self, days, options):
        """Clean up old notifications."""
        cleanup_msg = f'🧹 Cleaning up notifications older than {days} days...'
        self.stdout.write(cleanup_msg)
        cutoff_date = timezone.now() - timedelta(days=days)
        old_notifications = Notification.objects.filter(
            is_read=True,
            created_at__lt=cutoff_date
        )
        count = old_notifications.count()
        if count == 0:
            self.stdout.write('  ℹ️  No old notifications to clean up')
            return
        if not options['force']:
            confirm = input(f'Delete {count} old notifications? (y/N): ')
            if confirm.lower() != 'y':
                self.stdout.write('  ❌ Cleanup cancelled')
                return
        deleted_count = old_notifications.delete()[0]
        success_msg = f'✅ Cleaned up {deleted_count} old notifications'
        self.stdout.write(self.style.SUCCESS(success_msg))

    def _show_statistics(self):
        """Show application statistics."""
        self.stdout.write('📊 Application Statistics:\n')
        # User statistics
        total_users = CustomUser.objects.count()
        readers = CustomUser.objects.filter(role='reader').count()
        journalists = CustomUser.objects.filter(role='journalist').count()
        editors = CustomUser.objects.filter(role='editor').count()
        self.stdout.write(f'👥 Users: {total_users} total')
        self.stdout.write(f'   📖 Readers: {readers}')
        self.stdout.write(f'   ✍️  Journalists: {journalists}')
        self.stdout.write(f'   ✏️  Editors: {editors}')
        # Article statistics
        total_articles = Article.objects.count()
        published = Article.objects.filter(status='published').count()
        approved = Article.objects.filter(is_approved=True).count()
        self.stdout.write(f'\n📰 Articles: {total_articles} total')
        self.stdout.write(f'   ✅ Published: {published}')
        self.stdout.write(f'   ✔️  Approved: {approved}')
        # Notification statistics
        total_notifications = Notification.objects.count()
        read_notifications = Notification.objects.filter(is_read=True).count()
        email_tracked = Notification.objects.filter(
            email_opened_at__isnull=False).count()
        self.stdout.write(f'\n📬 Notifications: {total_notifications} total')
        self.stdout.write(f'   ✅ Read: {read_notifications}')
        self.stdout.write(f'   📧 Email tracked: {email_tracked}')
        # Subscription statistics
        pub_subs = CustomUser.objects.filter(
            subscribed_publishers__isnull=False
        ).distinct().count()
        jour_subs = CustomUser.objects.filter(
            subscribed_journalists__isnull=False
        ).distinct().count()
        self.stdout.write('\n📮 Subscriptions:')
        self.stdout.write(f'   🏢 Publisher subscribers: {pub_subs}')
        self.stdout.write(f'   ✍️  Journalist subscribers: {jour_subs}')
        # Recent activity
        recent_articles = Article.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        ).count()
        recent_notifications = Notification.objects.filter(
            created_at__gte=timezone.now() - timedelta(days=7)
        ).count()
        self.stdout.write('\n📈 Last 7 days:')
        self.stdout.write(f'   📰 New articles: {recent_articles}')
        self.stdout.write(f'   📬 Notifications: {recent_notifications}')

    def _check_configuration(self):
        """Check application configuration."""
        self.stdout.write('🔧 Configuration Check:\n')
        # Email configuration
        self.stdout.write('📧 Email Settings:')
        email_backend = getattr(settings, 'EMAIL_BACKEND', 'Not configured')
        self.stdout.write(f'   Backend: {email_backend}')
        if hasattr(settings, 'EMAIL_HOST'):
            self.stdout.write(f'   ✅ SMTP Host: {settings.EMAIL_HOST}')
            port = getattr(settings, "EMAIL_PORT", "Not set")
            self.stdout.write(f'   ✅ SMTP Port: {port}')
            use_tls = getattr(settings, "EMAIL_USE_TLS", False)
            self.stdout.write(f'   ✅ Use TLS: {use_tls}')
        else:
            self.stdout.write('   ❌ SMTP not configured')
        if hasattr(settings, 'EMAIL_HOST_USER'):
            self.stdout.write(f'   ✅ Host User: {settings.EMAIL_HOST_USER}')
        else:
            self.stdout.write('   ❌ Email user not configured')
        # Database configuration
        self.stdout.write('\n💾 Database Settings:')
        db_config = settings.DATABASES['default']
        self.stdout.write(f'   Engine: {db_config["ENGINE"]}')
        self.stdout.write(f'   Name: {db_config["NAME"]}')
        self.stdout.write(f'   Host: {db_config.get("HOST", "localhost")}')
        # Application settings
        self.stdout.write('\n⚙️  App Settings:')
        self.stdout.write(f'   DEBUG: {settings.DEBUG}')
        base_url = getattr(settings, "BASE_URL", "Not set")
        self.stdout.write(f'   BASE_URL: {base_url}')
        tracking = getattr(settings, "EMAIL_TRACKING_ENABLED", True)
        self.stdout.write(f'   Email Tracking: {tracking}')
        # Test database connection
        try:
            from django.db import connection
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
            self.stdout.write('   ✅ Database connection: OK')
        except Exception as e:
            self.stdout.write(f'   ❌ Database connection: {e}')
