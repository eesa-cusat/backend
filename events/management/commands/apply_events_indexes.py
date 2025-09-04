"""
Auto-apply Events module database indexes during deployment
This command runs automatically via Dockerfile
"""

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Apply Events module production indexes automatically'
    
    def handle(self, *args, **options):
        if connection.vendor != 'postgresql':
            self.stdout.write('Skipping Events indexes (not PostgreSQL)')
            return
        
        self.stdout.write('📅 Applying Events module indexes...')
        
        indexes = [
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_event_status_featured ON events_event (status, is_featured, is_active);", 
             "Event status and featured index"),
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_event_dates ON events_event (start_date, end_date);", 
             "Event dates index"),
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_event_type_status ON events_event (event_type, status, start_date DESC);", 
             "Event type and status index"),
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_event_registration ON events_event (registration_required, registration_deadline) WHERE status = 'published';", 
             "Event registration index"),
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_event_search ON events_event USING gin(to_tsvector('english', title || ' ' || description));", 
             "Event full-text search index"),
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_registration_event_status ON events_eventregistration (event_id, payment_status);", 
             "Event registration status index"),
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_registration_email ON events_eventregistration (email, registered_at DESC);", 
             "Registration email index"),
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_registration_payment ON events_eventregistration (payment_status, payment_date) WHERE payment_status != 'pending';", 
             "Registration payment index"),
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_notification_active ON events_notification (is_active, is_marquee, priority, created_at DESC);", 
             "Notification active index"),
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_notification_dates ON events_notification (start_date, end_date) WHERE is_active = true;", 
             "Notification dates index"),
        ]
        
        success_count = 0
        for sql, desc in indexes:
            try:
                with connection.cursor() as cursor:
                    cursor.execute(sql)
                self.stdout.write(f"✅ {desc}")
                success_count += 1
            except Exception as e:
                self.stdout.write(f"⚠️  {desc} - {str(e)}")
        
        self.stdout.write(f'📅 Events indexes: {success_count}/{len(indexes)} applied')
