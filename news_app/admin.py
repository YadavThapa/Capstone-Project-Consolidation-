"""Simplified admin configuration for news_app."""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin

from .models import (
    CustomUser,
    Article,
    Publisher,
    Newsletter,
    ContactMessage,
    Notification,
)


@admin.register(CustomUser)
class CustomUserAdmin(UserAdmin):
    """Admin for CustomUser with role-based group management."""

    list_display = (
        'username',
        'email',
        'role',
        'get_groups',
        'is_staff',
        'is_active'
    )
    list_filter = ('role', 'groups', 'is_staff', 'is_active')
    search_fields = ('username', 'email', 'first_name', 'last_name')
    ordering = ('username',)

    # Define fieldsets with custom fields
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email')}),
        ('Role & Profile', {
            'fields': ('role', 'bio', 'profile_picture', 'publisher')
        }),
        ('Permissions', {
            'fields': (
                'is_active',
                'is_staff',
                'is_superuser',
                'groups',
                'user_permissions'
            ),
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
        ('Subscriptions', {
            'fields': ('subscribed_publishers', 'subscribed_journalists'),
            'classes': ('collapse',)
        }),
    )

    filter_horizontal = (
        'subscribed_publishers',
        'subscribed_journalists',
        'groups',
        'user_permissions'
    )

    def get_groups(self, obj):
        """Display user's groups in admin list."""
        return ', '.join([group.name for group in obj.groups.all()]) or 'None'
    get_groups.short_description = 'Groups'  # type: ignore

    def save_model(self, request, obj, form, change):
        """Automatically assign user to appropriate group when saving."""
        super().save_model(request, obj, form, change)
        # Trigger group assignment
        obj.assign_group()


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """Admin for Article with basic list display."""

    list_display = (
        'title', 'author', 'status', 'is_approved', 'created_at'
    )
    list_filter = ('status', 'is_approved', 'created_at')
    search_fields = ('title', 'content', 'author__username')
    readonly_fields = ('created_at', 'updated_at')


@admin.register(ContactMessage)
class ContactMessageAdmin(admin.ModelAdmin):
    """Admin for ContactMessage records."""

    list_display = ('name', 'email', 'message_preview', 'created_at')
    search_fields = ('name', 'email', 'message')
    list_filter = ('created_at',)
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

    def message_preview(self, obj):
        """Show a preview of the message in the admin list."""
        if len(obj.message) > 50:
            return f"{obj.message[:50]}..."
        return obj.message
    message_preview.short_description = 'Message Preview'  # type: ignore


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    """Admin for notification records."""

    list_display = (
        'recipient', 'title', 'notification_type', 'is_read', 'created_at'
    )
    search_fields = ('title', 'message', 'recipient__username')
    list_filter = ('notification_type', 'is_read', 'created_at')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)

    def get_queryset(self, request):
        """Optimize queries by selecting related objects."""
        return super().get_queryset(request).select_related(
            'recipient', 'article'
        )


@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    """Admin for Publisher with comprehensive staff management."""

    list_display = (
        'name', 'website', 'founded_date', 'editor_count', 'journalist_count',
        'total_staff_count', 'created_at'
    )
    list_filter = ('founded_date', 'created_at')
    search_fields = ('name', 'description', 'website')
    readonly_fields = (
        'created_at',
        'updated_at',
        'editor_count',
        'journalist_count',
        'total_staff_count'
    )
    filter_horizontal = ('staff_members',)  # Main staff management field
    ordering = ('name',)

    fieldsets = (
        ('Basic Information', {
            'fields': (
                'name',
                'description',
                'website',
                'founded_date',
                'logo'
            )
        }),
        ('Staff Management', {
            'fields': ('staff_members',),
            'description': (
                'Select editors and journalists who work for this publisher. '
                'Use Ctrl+Click to select multiple staff members.'
            )
        }),
        ('Staff Statistics', {
            'fields': (
                'editor_count',
                'journalist_count',
                'total_staff_count'
            ),
            'classes': ('collapse',),
            'description': 'Read-only statistics about staff composition.'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )

    def formfield_for_manytomany(self, db_field, request, **kwargs):
        """Customize the queryset for staff selection fields."""
        if db_field.name == "staff_members":
            # Show both editors and journalists, grouped by role
            kwargs["queryset"] = (
                CustomUser.objects.filter(
                    role__in=['editor', 'journalist']
                ).order_by('role', 'username')
            )
        return super().formfield_for_manytomany(db_field, request, **kwargs)

    def editor_count(self, obj):
        """Show the number of editors for this publisher."""
        return obj.editor_count
    editor_count.short_description = 'Editors'  # type: ignore

    def journalist_count(self, obj):
        """Show the number of journalists for this publisher."""
        return obj.journalist_count
    journalist_count.short_description = 'Journalists'  # type: ignore

    def total_staff_count(self, obj):
        """Show the total number of staff members for this publisher."""
        return obj.total_staff_count
    total_staff_count.short_description = 'Total Staff'  # type: ignore


@admin.register(Newsletter)
class NewsletterAdmin(admin.ModelAdmin):
    """Admin for Newsletter records."""

    list_display = (
        'title',
        'author',
        'publisher',
        'is_independent',
        'sent_at',
        'created_at'
    )
    list_filter = ('is_independent', 'created_at', 'sent_at', 'publisher')
    search_fields = ('title', 'content', 'author__username')
    readonly_fields = ('created_at',)
    ordering = ('-created_at',)
