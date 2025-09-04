"""
Auto-apply Gallery module database indexes during deployment
This command runs automatically via Dockerfile
"""

from django.core.management.base import BaseCommand
from django.db import connection


class Command(BaseCommand):
    help = 'Apply Gallery module production indexes automatically'
    
    def handle(self, *args, **options):
        if connection.vendor != 'postgresql':
            self.stdout.write('Skipping Gallery indexes (not PostgreSQL)')
            return
        
        self.stdout.write('🖼️ Applying Gallery module indexes...')
        
        indexes = [
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_gallery_category_active ON gallery_gallerycategory (is_active, display_order);", 
             "Gallery category active index"),
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_gallery_album_category_featured ON gallery_galleryalbum (category_id, is_featured, is_active);", 
             "Gallery album category index"),
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_gallery_album_public ON gallery_galleryalbum (is_public, event_date DESC) WHERE is_active = true;", 
             "Gallery album public index"),
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_gallery_image_album_public ON gallery_galleryimage (album_id, is_public, is_featured);", 
             "Gallery image album index"),
            ("CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_gallery_image_search ON gallery_galleryimage USING gin(to_tsvector('english', title || ' ' || COALESCE(description, '') || ' ' || COALESCE(tags, '')));", 
             "Gallery image search index"),
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
        
        self.stdout.write(f'🖼️ Gallery indexes: {success_count}/{len(indexes)} applied')
