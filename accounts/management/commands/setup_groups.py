from django.core.management.base import BaseCommand
from django.contrib.auth.models import Group


class Command(BaseCommand):
    help = 'Create the required groups for EESA backend admin system'

    def handle(self, *args, **options):
        """Create the required groups for role-based permissions"""
        
        groups = [
            ('academics_team', 'Academics Team - Manages schemes, subjects, notes, and projects'),
            ('events_team', 'Events Team - Manages events and registrations'),
            ('careers_team', 'Careers Team - Manages job/internship posts'),
            ('people_team', 'People Team - Manages alumni data and team structure'),
        ]
        
        created_count = 0
        existing_count = 0
        
        for group_name, description in groups:
            group, created = Group.objects.get_or_create(name=group_name)
            
            if created:
                created_count += 1
                self.stdout.write(
                    self.style.SUCCESS(f'Created group: {group_name}')
                )
            else:
                existing_count += 1
                self.stdout.write(
                    self.style.WARNING(f'Group already exists: {group_name}')
                )
        
        self.stdout.write('')
        self.stdout.write(
            self.style.SUCCESS(f'Groups setup complete!')
        )
        self.stdout.write(f'Created: {created_count} groups')
        self.stdout.write(f'Existing: {existing_count} groups')
        self.stdout.write('')
        
        # Display group information
        self.stdout.write(self.style.HTTP_INFO('Group Permissions:'))
        self.stdout.write('• academics_team: Full CRUD access to Schemes, Subjects, Notes, Projects')
        self.stdout.write('• events_team: Full CRUD access to Events')
        self.stdout.write('• careers_team: Full CRUD access to Career/Job/Internship Posts')
        self.stdout.write('• people_team: Full CRUD access to Alumni data + EESA core team structure')
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('Next Steps:'))
        self.stdout.write('1. Assign users to appropriate groups via Django Admin')
        self.stdout.write('2. Users will automatically gain staff privileges when assigned to any group')
        self.stdout.write('3. Frontend admin panel will show sections based on user group membership')
