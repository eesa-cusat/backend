"""
Auto-apply Projects module database indexes during deployment
This command runs automatically via Dockerfile
"""

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Apply Projects module production indexes automatically'
    
    def handle(self, *args, **options):
        if connection.vendor != 'postgresql':
            self.stdout.write('Skipping Projects indexes (not PostgreSQL)')
            return
        
        self.stdout.write('💼 Applying Projects module indexes...')
        
        indexes = [
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_projects_project_category_featured ON projects_project (category, is_featured, is_published);", 
             "Project category and featured index"),
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_projects_project_published ON projects_project (is_published, created_at DESC) WHERE is_published = true;", 
             "Published projects index"),
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_projects_project_creator ON projects_project (created_by_id, created_at DESC);", 
             "Project creator index"),
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_projects_project_search ON projects_project USING gin(to_tsvector('english', title || ' ' || description || ' ' || COALESCE(abstract, '')));", 
             "Project full-text search index"),
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_projects_image_project_featured ON projects_projectimage (project_id, is_featured, created_at);", 
             "Project image featured index"),
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
        
        self.stdout.write(f'💼 Projects indexes: {success_count}/{len(indexes)} applied')
