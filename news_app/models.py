"""Django models for the news app.

This module defines Publisher, CustomUser, Article, Newsletter and
ContactMessage models.

Many dynamic Django attributes (managers and related objects) can
trigger static-analysis false positives. We disable some noisy checks
for this module to keep the code readable while acknowledging those
false positives at the type-checking layer.
"""
# pylint: disable=invalid-name,too-few-public-methods,
# pylint: disable=no-member,missing-function-docstring
# mypy: ignore-errors

from django.db import models
from django.contrib.auth.models import AbstractUser, Group
from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.core.exceptions import ValidationError
from django.utils.text import slugify
# no external regex dependencies needed for language heuristics

# Static analysis: Django model managers and related attributes are dynamic
# and commonly reported as false positives by Pylint/mypy. Disable noisy
# checks for this module. We also allow import-outside-toplevel for
# optional runtime imports and broad-exception-caught where a best-effort
# pylint: disable=E1101, no-member, import-error, import-outside-toplevel
# pylint: disable=broad-exception-caught, unused-argument
# pylint: disable=missing-class-docstring


# Roles used by the CustomUser model
ROLE_CHOICES = [
    ('reader', 'Reader'),
    ('journalist', 'Journalist'),
    ('editor', 'Editor'),
]


class Publisher(models.Model):
    """Publisher model - can have multiple editors and journalists"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True, null=True)
    founded_date = models.DateField(blank=True, null=True)
    logo = models.ImageField(
        upload_to='publishers/', blank=True, null=True
    )
    # Staff members field: allows selecting both editors and journalists
    # This is the primary relationship for managing publisher staff
    staff_members = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name='staff_publishers',
        blank=True,
        limit_choices_to={'role__in': ['editor', 'journalist']},
    )

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ['name']

    def __str__(self):
        # ensure we return a plain str
        return str(self.name)

    def get_editors(self):
        """Return QuerySet of editors working for this publisher."""
        return self.staff_members.filter(role='editor')

    def get_journalists(self):
        """Return QuerySet of journalists working for this publisher."""
        return self.staff_members.filter(role='journalist')

    def get_all_staff(self):
        """Return QuerySet of all staff members (editors and journalists)."""
        return self.staff_members.all()

    def add_editor(self, user):
        """Add an editor to this publisher's staff."""
        if user.role == 'editor':
            self.staff_members.add(user)
            return True
        return False

    def add_journalist(self, user):
        """Add a journalist to this publisher's staff."""
        if user.role == 'journalist':
            self.staff_members.add(user)
            return True
        return False

    def remove_staff_member(self, user):
        """Remove a staff member from this publisher."""
        self.staff_members.remove(user)

    @property
    def editor_count(self):
        """Count of editors working for this publisher."""
        return self.get_editors().count()

    @property
    def journalist_count(self):
        """Count of journalists working for this publisher."""
        return self.get_journalists().count()

    @property
    def staff_count(self):
        """Total count of staff members (editors + journalists)."""
        return self.staff_members.count()


def _is_mostly_english(text: str, threshold: float = 0.8) -> bool:
    """Quick heuristic to assert text is mostly English.

    Strategy:
    - Prefer using the `langdetect` package if available.
    - Otherwise fall back to a simple heuristic: count ASCII letters
      (A-Za-z) vs other letters; return True if ratio >= threshold.

    This avoids adding a hard runtime dependency but still provides
    reasonable protection against non-English content.
    """
    if not text:
        return True

    # try a reliable detector if present
    try:
        # Optional runtime import; mypy/Pylance may not have the package
        # available in the environment. Silence import-not-found for those
        # static checks.
        from langdetect import detect  # type: ignore[import-not-found]

        try:
            return detect(text) == 'en'
        except Exception:
            # fall through to heuristic
            pass
    except Exception:
        # langdetect not installed; fall back to the heuristic
        pass

    # heuristic: count ASCII/Latin letters vs all letter characters using
    # a Unicode-safe method that doesn't rely on unsupported regex escapes.
    letters = [ch for ch in text if 'A' <= ch <= 'Z' or 'a' <= ch <= 'z']
    all_letters = [ch for ch in text if ch.isalpha()]
    try:
        ratio = len(letters) / max(1, len(all_letters))
    except Exception:
        ratio = 1.0 if len(letters) else 0.0
    return ratio >= threshold


class CustomUser(AbstractUser):
    """Custom user with role and profile fields"""
    role = models.CharField(
        max_length=20,
        choices=ROLE_CHOICES,
        default='reader',
    )
    bio = models.TextField(blank=True, null=True)

    profile_picture = models.ImageField(
        upload_to='profiles/', blank=True, null=True
    )

    # Fields for Reader role
    subscribed_publishers = models.ManyToManyField(
        Publisher,
        related_name='subscribers',
        blank=True,
    )
    subscribed_journalists = models.ManyToManyField(
        'self',
        symmetrical=False,
        related_name='journalist_subscribers',
        blank=True,
        limit_choices_to={'role': 'journalist'},
    )

    # Fields for Journalist role
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='journalists',
    )

    @property
    def independent_articles(self):
        """QuerySet of this user's independently-published articles."""
        # uses the related_name 'authored_articles' defined on Article.author
        return self.authored_articles.filter(is_independent=True)

    @property
    def independent_newsletters(self):
        """QuerySet of this user's independently-published newsletters."""
        return self.authored_newsletters.filter(is_independent=True)

    def __str__(self):
        # get_role_display() is provided by Django; cast to str for linters
        return f"{self.username} ({str(self.get_role_display())})"

    def assign_group(self):
        """
        Assign user to a Django group based on role with specific permissions.

        Role-to-group mapping and permissions:
        - Reader: Can only view articles and newsletters
        - Editor: Can view, update, and delete articles and newsletters
        - Journalist: Can create, view, update, and delete articles and
          newsletters
        """
        # Clear existing groups and (re)assign according to the user's role.
        self.groups.clear()

        # Map role to a human-friendly group name (pluralized).
        role_map = {
            'reader': 'Readers',
            'journalist': 'Journalists',
            'editor': 'Editors',
        }

        group_name = role_map.get(self.role, self.role.capitalize())
        group, _ = Group.objects.get_or_create(name=group_name)

        # Determine permissions for each role based on requirements
        try:
            # Import here to avoid circular imports during app registry init
            from django.contrib.contenttypes.models import ContentType
            from django.contrib.auth.models import Permission

            article_ct = ContentType.objects.get_for_model(Article)
            newsletter_ct = ContentType.objects.get_for_model(Newsletter)

            if self.role == 'reader':
                # Reader: Can only view articles and newsletters
                perms = Permission.objects.filter(
                    content_type__in=[article_ct, newsletter_ct],
                    codename__in=['view_article', 'view_newsletter'],
                )
            elif self.role == 'editor':
                # Editor: Can view, update, and delete articles and newsletters
                perms = Permission.objects.filter(
                    content_type__in=[article_ct, newsletter_ct],
                    codename__in=[
                        'view_article',
                        'change_article',    # "update" is "change" in Django
                        'delete_article',
                        'view_newsletter',
                        'change_newsletter',
                        'delete_newsletter',
                    ],
                )
            elif self.role == 'journalist':
                # Journalist: Can create, view, update, and delete articles and
                # newsletters
                perms = Permission.objects.filter(
                    content_type__in=[article_ct, newsletter_ct],
                    codename__in=[
                        'add_article',       # "create" is "add" in Django
                        'view_article',
                        'change_article',    # "update" is "change" in Django
                        'delete_article',
                        'add_newsletter',
                        'view_newsletter',
                        'change_newsletter',
                        'delete_newsletter',
                    ],
                )
            else:
                perms = Permission.objects.none()

            group.permissions.set(perms)
        except Exception:
            # Skip assigning permissions during early migrations or unavailable
            # ContentType/Permission lookup — this will be retried via the
            # management command `sync_groups`.
            pass

        # Ensure the group is added; wrap in try/except for safety.
        try:
            self.groups.add(group)
        except Exception:
            # Be conservative: don't fail user save if group add errors occur.
            pass


# Signal to automatically assign groups when user is saved
@receiver(post_save, sender='news_app.CustomUser')
def assign_user_group(sender, instance, created, **kwargs):
    """Automatically assign user to appropriate group based on role."""
    instance.assign_group()


class ContactMessage(models.Model):
    name = models.CharField(max_length=120)
    email = models.EmailField()
    message = models.TextField()
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    def __str__(self):
        return f"{self.name} <{self.email}> - {self.created_at:%Y-%m-%d}"


class Notification(models.Model):
    """A simple notification record for users.

    Created when an article is approved so the UI can display unread
    notifications to users. Notifications are created for subscribers
    when an Article transitions to approved/published.
    """
    NOTIFICATION_TYPES = [
        ('publisher', 'Publisher Subscription'),
        ('journalist', 'Journalist Subscription'),
        ('general', 'General Notification'),
    ]

    recipient = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name='notifications',
    )
    article = models.ForeignKey(
        'Article',
        on_delete=models.CASCADE,
        related_name='notifications',
        null=True,
        blank=True,
    )
    title = models.CharField(max_length=300)
    message = models.TextField()
    notification_type = models.CharField(
        max_length=20,
        choices=NOTIFICATION_TYPES,
        default='general',
        help_text='Source: publisher or journalist subscription'
    )
    is_read = models.BooleanField(default=False)
    email_opened_at = models.DateTimeField(
        null=True, blank=True,
        help_text='Timestamp when email was opened/read'
    )
    read_token = models.CharField(
        max_length=64, unique=True, blank=True,
        help_text='Unique token for email read tracking'
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    # For static analysis tools (Mypy/Pylint)
    id: int

    class Meta:
        ordering = ['-created_at']

    def save(self, *args, **kwargs):
        """Generate read token if not exists."""
        if not self.read_token:
            import uuid
            self.read_token = str(uuid.uuid4()).replace('-', '')
        super().save(*args, **kwargs)

    def mark_as_read(self):
        """Mark notification as read with timestamp."""
        from django.utils import timezone
        if not self.is_read:
            self.is_read = True
            self.email_opened_at = timezone.now()
            self.save()

    def __str__(self) -> str:
        type_display = self.get_notification_type_display()
        title = str(self.title)
        if len(title) > 50:
            title = title[:50] + '...'
        return f"Notification to {self.recipient} - {title} ({type_display})"


class Category(models.Model):
    """News category model for organizing articles"""

    name = models.CharField(max_length=100, unique=True)
    slug = models.SlugField(max_length=100, unique=True)
    description = models.TextField(blank=True)
    color = models.CharField(max_length=7, default='#007bff')  # Hex color
    icon = models.CharField(
        max_length=50, blank=True
    )  # FontAwesome icon class
    order = models.IntegerField(default=0)  # For ordering in navigation
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Categories"
        ordering = ['order', 'name']

    def __str__(self) -> str:
        return str(self.name)

    def save(self, *args, **kwargs):
        if not self.slug:
            self.slug = slugify(self.name)
        super().save(*args, **kwargs)

    def get_absolute_url(self):
        """Get URL for this category"""
        from django.urls import reverse
        return reverse('article_list') + f'?category={self.slug}'

    @property
    def article_count(self):
        """Count of articles in this category"""
        return self.articles.filter(
            status='approved', is_approved=True
        ).count()


class Article(models.Model):
    """Article model with approval workflow"""

    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('pending', 'Pending Approval'),
        ('approved', 'Approved'),
        ('rejected', 'Rejected'),
        ('published', 'Published'),
    ]

    title = models.CharField(max_length=300)
    slug = models.SlugField(max_length=250, unique=True)
    content = models.TextField()
    summary = models.TextField(max_length=500)
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='authored_articles',
        limit_choices_to={'role': 'journalist'}
    )
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.CASCADE,
        related_name='articles',
        null=True,
        blank=True,
    )
    category = models.ForeignKey(
        Category,
        on_delete=models.SET_NULL,
        related_name='articles',
        null=True,
        blank=True,
    )
    status = models.CharField(
        max_length=20,
        choices=STATUS_CHOICES,
        default='draft',
    )
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        CustomUser,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_articles',
        limit_choices_to={'role': 'editor'},
    )
    approved_at = models.DateTimeField(
        null=True, blank=True
    )
    is_independent = models.BooleanField(default=False)
    featured_image = models.ImageField(
        upload_to='articles/', blank=True, null=True
    )
    tags = models.CharField(max_length=200, blank=True)
    source_url = models.URLField(blank=True, null=True)
    source_image_url = models.URLField(blank=True, null=True)
    views_count = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(
        null=True, blank=True
    )

    class Meta:
        ordering = ['-created_at']
        permissions = [
            ('approve_article', 'Can approve articles'),
        ]

    def __str__(self):
        return str(self.title)

    def clean(self) -> None:
        """Validate that content and summary are mostly English.

        Raises a ValidationError when non-English text is detected. This
        method is intentionally fast and conservative to avoid blocking
        legitimate content in edge cases.
        """
        errors = {}
        if not _is_mostly_english(self.title):
            errors['title'] = 'Title must be in English.'
        if not _is_mostly_english(self.summary):
            errors['summary'] = 'Summary must be in English.'
        if not _is_mostly_english(self.content, threshold=0.6):
            errors['content'] = 'Content must be primarily English.'
        if errors:
            raise ValidationError(errors)

    def get_subscribers(self):
        """Get all subscribers who should receive this article"""
        subscribers = set()

        # Get publisher subscribers
        if self.publisher:
            pub_subs = self.publisher.subscribers.filter(email__isnull=False)
            subscribers.update(pub_subs)

        # Get journalist subscribers
        subscribers.update(
            self.author.journalist_subscribers.filter(email__isnull=False)
        )

        return list(subscribers)

    def get_subscribers_by_type(self):
        """Get subscribers organized by subscription type.

        Returns:
            dict: {
                'publisher': QuerySet of publisher subscribers,
                'journalist': QuerySet of journalist subscribers,
                'all': combined list of unique subscribers
            }
        """
        result = {
            'publisher': None,
            'journalist': None,
            'all': []
        }

        # Get publisher subscribers
        if self.publisher:
            result['publisher'] = self.publisher.subscribers.filter(
                email__isnull=False
            )
        else:
            from django.db.models import QuerySet
            result['publisher'] = QuerySet(model=CustomUser).none()

        # Get journalist subscribers
        result['journalist'] = self.author.journalist_subscribers.filter(
            email__isnull=False
        )

        # Combine all unique subscribers
        all_subscribers = set()
        if result['publisher']:
            all_subscribers.update(result['publisher'])
        all_subscribers.update(result['journalist'])
        result['all'] = list(all_subscribers)

        return result


class Newsletter(models.Model):
    """Newsletter model"""

    title = models.CharField(max_length=300)
    content = models.TextField()
    author = models.ForeignKey(
        CustomUser,
        on_delete=models.CASCADE,
        related_name='authored_newsletters',
        limit_choices_to={'role__in': ['journalist', 'editor']}
    )
    publisher = models.ForeignKey(
        Publisher,
        on_delete=models.CASCADE,
        related_name='newsletters',
        null=True,
        blank=True,
    )
    is_independent = models.BooleanField(default=False)
    sent_at = models.DateTimeField(
        null=True, blank=True
    )
    created_at = models.DateTimeField(
        auto_now_add=True
    )

    class Meta:
        ordering = ['-created_at']

    def __str__(self):
        return str(self.title)

    def clean(self) -> None:
        """Ensure newsletter title and content are mostly English."""
        errors = {}
        if not _is_mostly_english(self.title):
            errors['title'] = 'Title must be in English.'
        if not _is_mostly_english(self.content, threshold=0.6):
            errors['content'] = 'Content must be primarily English.'
        if errors:
            raise ValidationError(errors)


# Ensure role-specific fields are consistent after user save.
@receiver(post_save, sender=CustomUser)
def ensure_role_fields(sender, instance, **kwargs):
    """If user is a journalist, clear reader-only fields; if reader, clear
    journalist-only fields. This keeps the model state consistent with role.
    """
    changed = False
    if instance.role == 'journalist':
        # Journalist shouldn't have reader subscription lists
        if instance.subscribed_publishers.exists():
            instance.subscribed_publishers.clear()
            changed = True
        if instance.subscribed_journalists.exists():
            instance.subscribed_journalists.clear()
            changed = True
    elif instance.role == 'reader':
        # Reader shouldn't be attached to a publisher as journalist
        if instance.publisher is not None:
            instance.publisher = None
            changed = True

    if changed:
        instance.save()


@receiver(post_save, sender=CustomUser)
def assign_group_on_save(sender, instance, created, **kwargs):
    """After a CustomUser is saved, ensure Group/permissions match role.

    This lightweight sync will silently skip on early-migration phases
    where ContentType/Permission objects may not yet exist.
    """
    try:
        instance.assign_group()
    except Exception:
        # Don't allow permission assignment failures to interrupt user saves
        pass
