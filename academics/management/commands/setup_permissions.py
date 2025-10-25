"""
Django Management Command: Setup Permission Groups
Creates and configures permission groups for the EESA backend system.

Groups Created:
1. Events & Gallery Manager - Manage events and gallery
2. Academics & Projects Manager - Manage academics and projects
3. Careers & Placements Manager - Manage careers and placements
4. Teacher - All permissions except account management
5. Admin - Full access including accounts

Usage:
    python manage.py setup_permissions
    python manage.py setup_permissions --reset  # Delete and recreate all groups
"""

from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group, Permission
from django.contrib.contenttypes.models import ContentType
from django.apps import apps


class Command(BaseCommand):
    help = 'Create and configure permission groups for EESA backend'

    def add_arguments(self, parser):
        parser.add_argument(
            '--reset',
            action='store_true',
            help='Delete existing groups and recreate them',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('🔐 EESA Permission Groups Setup'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))

        if options['reset']:
            self.stdout.write(self.style.WARNING('⚠️  Reset mode: Deleting existing groups...'))
            Group.objects.filter(name__in=[
                'Events & Gallery Manager',
                'Academics & Projects Manager',
                'Careers & Placements Manager',
                'Teacher',
                'Admin'
            ]).delete()
            self.stdout.write(self.style.SUCCESS('✓ Existing groups deleted\n'))

        # Create groups
        self.create_events_gallery_manager()
        self.create_academics_projects_manager()
        self.create_careers_placements_manager()
        self.create_teacher_group()
        self.create_admin_group()

        self.stdout.write(self.style.SUCCESS('\n' + '='*70))
        self.stdout.write(self.style.SUCCESS('✅ Permission groups setup completed successfully!'))
        self.stdout.write(self.style.SUCCESS('='*70 + '\n'))

    def create_events_gallery_manager(self):
        """Create Events & Gallery Manager group"""
        self.stdout.write('\n📅 Creating Events & Gallery Manager group...')
        
        group, created = Group.objects.get_or_create(name='Events & Gallery Manager')
        
        # Get all permissions for events and gallery apps
        events_permissions = Permission.objects.filter(
            content_type__app_label='events'
        )
        gallery_permissions = Permission.objects.filter(
            content_type__app_label='gallery'
        )
        
        # Add permissions
        group.permissions.set(list(events_permissions) + list(gallery_permissions))
        
        self.stdout.write(self.style.SUCCESS(
            f'  ✓ {"Created" if created else "Updated"} Events & Gallery Manager '
            f'({events_permissions.count() + gallery_permissions.count()} permissions)'
        ))
        self._display_permissions(group)

    def create_academics_projects_manager(self):
        """Create Academics & Projects Manager group"""
        self.stdout.write('\n📚 Creating Academics & Projects Manager group...')
        
        group, created = Group.objects.get_or_create(name='Academics & Projects Manager')
        
        # Get all permissions for academics and projects apps
        academics_permissions = Permission.objects.filter(
            content_type__app_label='academics'
        )
        projects_permissions = Permission.objects.filter(
            content_type__app_label='projects'
        )
        
        # Add permissions
        group.permissions.set(list(academics_permissions) + list(projects_permissions))
        
        self.stdout.write(self.style.SUCCESS(
            f'  ✓ {"Created" if created else "Updated"} Academics & Projects Manager '
            f'({academics_permissions.count() + projects_permissions.count()} permissions)'
        ))
        self._display_permissions(group)

    def create_careers_placements_manager(self):
        """Create Careers & Placements Manager group"""
        self.stdout.write('\n💼 Creating Careers & Placements Manager group...')
        
        group, created = Group.objects.get_or_create(name='Careers & Placements Manager')
        
        # Get all permissions for careers and placements apps
        careers_permissions = Permission.objects.filter(
            content_type__app_label='careers'
        )
        placements_permissions = Permission.objects.filter(
            content_type__app_label='placements'
        )
        
        # Add permissions
        group.permissions.set(list(careers_permissions) + list(placements_permissions))
        
        self.stdout.write(self.style.SUCCESS(
            f'  ✓ {"Created" if created else "Updated"} Careers & Placements Manager '
            f'({careers_permissions.count() + placements_permissions.count()} permissions)'
        ))
        self._display_permissions(group)

    def create_teacher_group(self):
        """Create Teacher group - all permissions except account management"""
        self.stdout.write('\n👨‍🏫 Creating Teacher group...')
        
        group, created = Group.objects.get_or_create(name='Teacher')
        
        # Get all permissions EXCEPT accounts app
        all_permissions = Permission.objects.exclude(
            content_type__app_label__in=['auth', 'accounts', 'contenttypes', 'sessions']
        )
        
        # Add permissions
        group.permissions.set(all_permissions)
        
        self.stdout.write(self.style.SUCCESS(
            f'  ✓ {"Created" if created else "Updated"} Teacher '
            f'({all_permissions.count()} permissions)'
        ))
        self.stdout.write('  📋 Includes: academics, alumni, careers, events, gallery, placements, projects')
        self.stdout.write('  🚫 Excludes: auth, accounts, contenttypes, sessions')
        self._display_permissions(group)

    def create_admin_group(self):
        """Create Admin group - full access including accounts"""
        self.stdout.write('\n👑 Creating Admin group...')
        
        group, created = Group.objects.get_or_create(name='Admin')
        
        # Get ALL permissions
        all_permissions = Permission.objects.all()
        
        # Add permissions
        group.permissions.set(all_permissions)
        
        self.stdout.write(self.style.SUCCESS(
            f'  ✓ {"Created" if created else "Updated"} Admin '
            f'({all_permissions.count()} permissions)'
        ))
        self.stdout.write('  📋 Full access to all apps including user/account management')
        self._display_permissions(group)

    def _display_permissions(self, group):
        """Display permissions by app for a group"""
        permissions = group.permissions.all()
        apps_dict = {}
        
        for perm in permissions:
            app_label = perm.content_type.app_label
            if app_label not in apps_dict:
                apps_dict[app_label] = []
            apps_dict[app_label].append(perm.codename)
        
        for app_label, perms in sorted(apps_dict.items()):
            self.stdout.write(f'    • {app_label}: {len(perms)} permissions')
