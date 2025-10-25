"""
Management command to create user groups with specific permissions
Creates groups for different app combinations and roles
"""
from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType


class Command(BaseCommand):
    help = 'Create user groups with specific permissions for EESA backend'

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n🚀 Setting up user groups and permissions...\n'))
        
        # Define groups and their associated apps
        group_configs = {
            'Events & Gallery Manager': {
                'description': 'Manage events and gallery content',
                'apps': ['events', 'gallery'],
                'exclude_accounts': True,
            },
            'Academics & Projects Manager': {
                'description': 'Manage academic resources and student projects',
                'apps': ['academics', 'projects'],
                'exclude_accounts': True,
            },
            'Careers & Placements Manager': {
                'description': 'Manage career opportunities and placement drives',
                'apps': ['careers', 'placements'],
                'exclude_accounts': True,
            },
            'Teacher': {
                'description': 'Full access to all modules except account management',
                'apps': ['academics', 'projects', 'events', 'gallery', 'careers', 'placements', 'alumni'],
                'exclude_accounts': True,
                'include_view_accounts': True,  # Can view but not add/change users
            },
            'Administrator': {
                'description': 'Full access to all features including account management',
                'apps': ['academics', 'projects', 'events', 'gallery', 'careers', 'placements', 'alumni', 'accounts'],
                'exclude_accounts': False,
                'full_access': True,
            },
        }
        
        for group_name, config in group_configs.items():
            self.create_or_update_group(group_name, config)
        
        self.stdout.write(self.style.SUCCESS('\n✅ All groups created successfully!\n'))
        self.print_summary()

    def create_or_update_group(self, group_name, config):
        """Create or update a group with specified permissions"""
        group, created = Group.objects.get_or_create(name=group_name)
        
        if created:
            self.stdout.write(self.style.SUCCESS(f'✨ Created group: {group_name}'))
        else:
            self.stdout.write(self.style.WARNING(f'📝 Updating existing group: {group_name}'))
            group.permissions.clear()
        
        self.stdout.write(f'   Description: {config["description"]}')
        
        # Get permissions for specified apps
        permissions = self.get_permissions_for_apps(
            config['apps'],
            exclude_accounts=config.get('exclude_accounts', False),
            include_view_accounts=config.get('include_view_accounts', False),
            full_access=config.get('full_access', False)
        )
        
        # Add permissions to group
        group.permissions.add(*permissions)
        
        self.stdout.write(self.style.SUCCESS(f'   ✅ Added {len(permissions)} permissions\n'))

    def get_permissions_for_apps(self, app_labels, exclude_accounts=False, include_view_accounts=False, full_access=False):
        """Get all permissions for specified apps"""
        permissions = []
        
        for app_label in app_labels:
            # Get all content types for this app
            content_types = ContentType.objects.filter(app_label=app_label)
            
            for content_type in content_types:
                # Get all permissions for this content type
                app_permissions = Permission.objects.filter(content_type=content_type)
                
                # Handle account restrictions
                if exclude_accounts and app_label == 'auth':
                    if include_view_accounts:
                        # Only view permissions for users and groups
                        app_permissions = app_permissions.filter(codename__startswith='view_')
                    else:
                        # Skip auth app entirely
                        continue
                
                # Handle accounts app restrictions
                if exclude_accounts and app_label == 'accounts':
                    if include_view_accounts:
                        app_permissions = app_permissions.filter(codename__startswith='view_')
                    else:
                        continue
                
                permissions.extend(app_permissions)
        
        # For Administrator, also add auth permissions
        if full_access:
            auth_permissions = Permission.objects.filter(
                content_type__app_label='auth'
            )
            permissions.extend(auth_permissions)
        
        return permissions

    def print_summary(self):
        """Print a summary of all groups and their permission counts"""
        self.stdout.write(self.style.SUCCESS('═' * 70))
        self.stdout.write(self.style.SUCCESS('📊 GROUPS SUMMARY'))
        self.stdout.write(self.style.SUCCESS('═' * 70))
        
        groups = Group.objects.all().order_by('name')
        for group in groups:
            perm_count = group.permissions.count()
            self.stdout.write(f'\n👥 {group.name}')
            self.stdout.write(f'   Permissions: {perm_count}')
            
            # List some sample permissions
            sample_perms = group.permissions.all()[:5]
            if sample_perms:
                self.stdout.write('   Sample permissions:')
                for perm in sample_perms:
                    self.stdout.write(f'      • {perm.name}')
        
        self.stdout.write(self.style.SUCCESS('\n' + '═' * 70))
        self.stdout.write(self.style.SUCCESS('\n💡 Usage Instructions:'))
        self.stdout.write('   1. Go to Django Admin → Users')
        self.stdout.write('   2. Select a user and assign them to appropriate group(s)')
        self.stdout.write('   3. Save the user')
        self.stdout.write(self.style.SUCCESS('\n' + '═' * 70 + '\n'))
