"""Management command to sync user groups and permissions based on roles."""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from news_app.models import CustomUser, Article, Newsletter


class Command(BaseCommand):
    help = 'Sync user groups and permissions based on roles'

    def add_arguments(self, parser):
        parser.add_argument(
            '--create-groups',
            action='store_true',
            help='Create groups and assign permissions',
        )
        parser.add_argument(
            '--assign-users',
            action='store_true',
            help='Assign all users to appropriate groups',
        )
        parser.add_argument(
            '--show-permissions',
            action='store_true',
            help='Show current group permissions',
        )

    def handle(self, *args, **options):
        if options['create_groups']:
            self.create_groups_and_permissions()
        
        if options['assign_users']:
            self.assign_users_to_groups()
            
        if options['show_permissions']:
            self.show_group_permissions()
            
        if not any([options['create_groups'], options['assign_users'], options['show_permissions']]):
            # Default: do everything
            self.create_groups_and_permissions()
            self.assign_users_to_groups()
            self.show_group_permissions()

    def create_groups_and_permissions(self):
        """Create groups and assign appropriate permissions."""
        self.stdout.write('Creating groups and assigning permissions...')
        
        # Get content types
        article_ct = ContentType.objects.get_for_model(Article)
        newsletter_ct = ContentType.objects.get_for_model(Newsletter)
        
        # Define role permissions according to requirements
        role_permissions = {
            'Readers': {
                'description': 'Can only view articles and newsletters',
                'permissions': [
                    'view_article',
                    'view_newsletter',
                ]
            },
            'Editors': {
                'description': 'Can view, update, and delete articles and newsletters',
                'permissions': [
                    'view_article',
                    'change_article',  # "update" in Django is "change"
                    'delete_article',
                    'view_newsletter',
                    'change_newsletter',
                    'delete_newsletter',
                ]
            },
            'Journalists': {
                'description': 'Can create, view, update, and delete articles and newsletters', 
                'permissions': [
                    'add_article',     # "create" in Django is "add"
                    'view_article',
                    'change_article',  # "update" in Django is "change"
                    'delete_article',
                    'add_newsletter',
                    'view_newsletter',
                    'change_newsletter',
                    'delete_newsletter',
                ]
            }
        }
        
        for group_name, config in role_permissions.items():
            # Create or get the group
            group, created = Group.objects.get_or_create(name=group_name)
            action = "Created" if created else "Updated"
            
            self.stdout.write(f'  {action} group: {group_name}')
            self.stdout.write(f'    Description: {config["description"]}')
            
            # Get permissions for this group
            permissions = Permission.objects.filter(
                content_type__in=[article_ct, newsletter_ct],
                codename__in=config['permissions']
            )
            
            # Assign permissions to group
            group.permissions.set(permissions)
            
            self.stdout.write(f'    Assigned {permissions.count()} permissions:')
            for perm in permissions:
                self.stdout.write(f'      - {perm.name} ({perm.codename})')
            
            self.stdout.write('')

    def assign_users_to_groups(self):
        """Assign all users to appropriate groups based on their roles."""
        self.stdout.write('Assigning users to groups based on roles...')
        
        # Role to group mapping
        role_group_map = {
            'reader': 'Readers',
            'journalist': 'Journalists', 
            'editor': 'Editors',
            'publisher_admin': 'Editors',  # Publisher admins get editor permissions
        }
        
        users = CustomUser.objects.all()
        updated_count = 0
        
        for user in users:
            group_name = role_group_map.get(user.role)
            if group_name:
                try:
                    group = Group.objects.get(name=group_name)
                    # Clear existing groups and add the appropriate one
                    user.groups.clear()
                    user.groups.add(group)
                    updated_count += 1
                    self.stdout.write(f'  Assigned {user.username} ({user.role}) to {group_name}')
                except Group.DoesNotExist:
                    self.stdout.write(
                        self.style.ERROR(f'  Group {group_name} does not exist for user {user.username}')
                    )
            else:
                self.stdout.write(
                    self.style.WARNING(f'  No group mapping for role: {user.role} (user: {user.username})')
                )
        
        self.stdout.write(f'\nUpdated {updated_count} users')

    def show_group_permissions(self):
        """Display current group permissions."""
        self.stdout.write('\nCurrent Group Permissions:')
        self.stdout.write('=' * 50)
        
        for group in Group.objects.all().order_by('name'):
            self.stdout.write(f'\n{group.name}:')
            permissions = group.permissions.all().order_by('content_type__model', 'codename')
            
            if permissions:
                for perm in permissions:
                    self.stdout.write(f'  - {perm.name} ({perm.codename})')
            else:
                self.stdout.write('  - No permissions assigned')
                
            # Show users in this group
            users = group.user_set.all()
            if users:
                self.stdout.write(f'  Users ({users.count()}): {", ".join([u.username for u in users])}')
            else:
                self.stdout.write('  Users: None')