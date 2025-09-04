"""
Auto-apply Placements module database indexes during deployment
This command runs automatically via Dockerfile
"""

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Apply Placements module production indexes automatically'
    
    def handle(self, *args, **options):
        if connection.vendor != 'postgresql':
            self.stdout.write('Skipping Placements indexes (not PostgreSQL)')
            return
        
        self.stdout.write('💼 Applying Placements module indexes...')
        
        indexes = [
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_placements_company_active ON placements_company (is_active, is_verified, created_at DESC);", 
             "Company active and verified index"),
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_placements_company_search ON placements_company USING gin(to_tsvector('english', name || ' ' || COALESCE(industry, '') || ' ' || COALESCE(location, '')));", 
             "Company search index"),
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_placements_drive_company_active ON placements_placementdrive (company_id, is_active, drive_date DESC);", 
             "Placement drive company index"),
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_placements_drive_dates ON placements_placementdrive (registration_start, registration_end, drive_date);", 
             "Placement drive dates index"),
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_placements_drive_featured ON placements_placementdrive (is_featured, is_active, drive_date DESC);", 
             "Placement drive featured index"),
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_placements_drive_search ON placements_placementdrive USING gin(to_tsvector('english', title || ' ' || description));", 
             "Placement drive search index"),
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_placements_application_drive_status ON placements_placementapplication (drive_id, status, applied_at DESC);", 
             "Placement application status index"),
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_placements_application_student ON placements_placementapplication (student_id, applied_at DESC);", 
             "Placement application student index"),
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_placements_placed_company_year ON placements_placedstudent (company_id, batch_year, package_lpa DESC);", 
             "Placed student company index"),
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_placements_placed_package ON placements_placedstudent (package_lpa DESC, offer_date DESC) WHERE is_verified = true AND is_active = true;", 
             "Placed student package index"),
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
        
        self.stdout.write(f'💼 Placements indexes: {success_count}/{len(indexes)} applied')
