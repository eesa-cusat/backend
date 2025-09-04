from django.core.management.base import BaseCommand
from django.db import connection
from django.apps import apps


class Command(BaseCommand):
    help = 'Add database indexes for better query performance'

    def handle(self, *args, **options):
        """Add custom indexes for frequently queried fields"""
        
        with connection.cursor() as cursor:
            self.stdout.write(self.style.HTTP_INFO('Adding performance indexes...'))
            
            # Indexes for User model (accounts app)
            try:
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_user_groups_lookup 
                    ON accounts_user_groups (user_id, group_id);
                """)
                self.stdout.write(self.style.SUCCESS('✓ Added user groups lookup index'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'User groups index: {e}'))

            # Indexes for Academic Resources (most queried)
            try:
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_academic_resources_public 
                    ON academics_academicresource (is_approved, is_active, created_at DESC)
                    WHERE is_approved = true AND is_active = true;
                """)
                self.stdout.write(self.style.SUCCESS('✓ Added academic resources public index'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Academic resources index: {e}'))

            # Composite index for subject filtering
            try:
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_academic_subject_filter 
                    ON academics_academicresource (subject_id, category, is_approved, created_at DESC);
                """)
                self.stdout.write(self.style.SUCCESS('✓ Added subject filtering index'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Subject filtering index: {e}'))

            # Indexes for Events (frequently accessed)
            try:
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_events_public_upcoming 
                    ON events_event (start_date, is_active, status)
                    WHERE is_active = true AND status = 'published';
                """)
                self.stdout.write(self.style.SUCCESS('✓ Added events public/upcoming index'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Events index: {e}'))

            # Indexes for Event Registrations
            try:
                cursor.execute("""
                    CREATE INDEX IF NOT EXISTS idx_event_registrations_lookup 
                    ON events_eventregistration (event_id, email, registered_at DESC);
                """)
                self.stdout.write(self.style.SUCCESS('✓ Added event registrations index'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'Event registrations index: {e}'))

            # Analyze tables for query optimization (PostgreSQL)
            if connection.vendor == 'postgresql':
                try:
                    cursor.execute("ANALYZE;")
                    self.stdout.write(self.style.SUCCESS('✓ Analyzed database statistics'))
                except Exception as e:
                    self.stdout.write(self.style.WARNING(f'Database analysis: {e}'))

            self.stdout.write('')
            self.stdout.write(self.style.SUCCESS('Database optimization complete!'))
            self.stdout.write(self.style.HTTP_INFO('Performance improvements:'))
            self.stdout.write('• Faster user permission lookups')
            self.stdout.write('• Optimized academic resource queries')
            self.stdout.write('• Improved event listing performance')
            self.stdout.write('• Enhanced registration lookups')
