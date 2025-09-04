"""
Auto-apply Careers module database indexes during deployment
This command runs automatically via Dockerfile
"""

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Apply Careers module production indexes automatically'
    
    def handle(self, *args, **options):
        if connection.vendor != 'postgresql':
            self.stdout.write('Skipping Careers indexes (not PostgreSQL)')
            return
        
        self.stdout.write('💼 Applying Careers module indexes...')
        
        indexes = [
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_careers_job_active_posted ON careers_jobopportunity (is_active, posted_at DESC);", 
             "Job opportunity active index"),
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_careers_job_type_level ON careers_jobopportunity (job_type, experience_level, posted_at DESC) WHERE is_active = true;", 
             "Job opportunity type index"),
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_careers_job_deadline ON careers_jobopportunity (application_deadline) WHERE application_deadline IS NOT NULL AND is_active = true;", 
             "Job opportunity deadline index"),
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_careers_job_search ON careers_jobopportunity USING gin(to_tsvector('english', title || ' ' || company || ' ' || location || ' ' || skills));", 
             "Job opportunity search index"),
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_careers_internship_active ON careers_internshipopportunity (is_active, posted_at DESC);", 
             "Internship opportunity active index"),
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_careers_internship_type_remote ON careers_internshipopportunity (internship_type, is_remote, start_date) WHERE is_active = true;", 
             "Internship opportunity type index"),
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_careers_internship_search ON careers_internshipopportunity USING gin(to_tsvector('english', title || ' ' || company || ' ' || location || ' ' || skills));", 
             "Internship opportunity search index"),
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_careers_certificate_active ON careers_certificateopportunity (is_active, posted_at DESC);", 
             "Certificate opportunity active index"),
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_careers_certificate_free_aid ON careers_certificateopportunity (is_free, financial_aid_available, validity_till) WHERE is_active = true;", 
             "Certificate opportunity free aid index"),
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_careers_certificate_provider ON careers_certificateopportunity (provider, certificate_type, posted_at DESC);", 
             "Certificate opportunity provider index"),
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_careers_certificate_search ON careers_certificateopportunity USING gin(to_tsvector('english', title || ' ' || provider || ' ' || skills_covered));", 
             "Certificate opportunity search index"),
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
        
        self.stdout.write(f'💼 Careers indexes: {success_count}/{len(indexes)} applied')
