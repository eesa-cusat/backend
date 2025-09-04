"""
Auto-apply Alumni module database indexes during deployment
This command runs automatically via Dockerfile
"""

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Apply Alumni module production indexes automatically'
    
    def handle(self, *args, **options):
        if connection.vendor != 'postgresql':
            self.stdout.write('Skipping Alumni indexes (not PostgreSQL)')
            return
        
        self.stdout.write('🎓 Applying Alumni module indexes...')
        
        indexes = [
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alumni_passout_employment ON alumni_alumni (year_of_passout, employment_status, is_active);", 
             "Alumni passout and employment index"),
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alumni_company_location ON alumni_alumni (current_company, current_location) WHERE current_company IS NOT NULL;", 
             "Alumni company and location index"),
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alumni_mentor_contact ON alumni_alumni (willing_to_mentor, allow_contact_from_juniors) WHERE is_active = true;", 
             "Alumni mentor contact index"),
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alumni_search ON alumni_alumni USING gin(to_tsvector('english', full_name || ' ' || COALESCE(current_company, '') || ' ' || COALESCE(job_title, '')));", 
             "Alumni full-text search index"),
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alumni_batch_scheme ON alumni_alumni (year_of_passout, scheme, year_of_joining);", 
             "Alumni batch and scheme index"),
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
        
        self.stdout.write(f'🎓 Alumni indexes: {success_count}/{len(indexes)} applied')
