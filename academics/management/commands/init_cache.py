"""
Django management command to create cache table and warm up caches
"""

from django.core.management.base import BaseCommand
from django.core.management import call_command
from django.core.cache import cache
from django.conf import settings


class Command(BaseCommand):
    help = 'Initialize cache system for production'

    def add_arguments(self, parser):
        parser.add_argument(
            '--warm-cache',
            action='store_true',
            help='Warm up the cache with frequently accessed data',
        )

    def handle(self, *args, **options):
        self.stdout.write(self.style.SUCCESS('🚀 Initializing cache system...'))
        
        # Create cache table if using database cache
        if 'DatabaseCache' in str(settings.CACHES['default']['BACKEND']):
            try:
                call_command('createcachetable', 'eesa_cache_table', verbosity=0)
                self.stdout.write(self.style.SUCCESS('✅ Cache table created successfully'))
            except Exception as e:
                self.stdout.write(self.style.WARNING(f'⚠️ Cache table creation: {str(e)}'))
        
        # Test cache connectivity
        try:
            cache.set('test_key', 'test_value', 60)
            if cache.get('test_key') == 'test_value':
                self.stdout.write(self.style.SUCCESS('✅ Cache system is working'))
                cache.delete('test_key')
            else:
                self.stdout.write(self.style.ERROR('❌ Cache system test failed'))
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Cache system error: {str(e)}'))
        
        # Warm cache if requested
        if options['warm_cache']:
            self.warm_up_cache()
    
    def warm_up_cache(self):
        """Pre-populate cache with frequently accessed data"""
        self.stdout.write(self.style.SUCCESS('🔥 Warming up cache...'))
        
        try:
            # Import here to avoid circular imports
            from academics.models import AcademicResource, Subject, Scheme
            from events.models import Event
            from projects.models import Project
            from gallery.models import GalleryImage, GalleryAlbum
            
            # Cache academic data
            schemes = list(Scheme.objects.filter(is_active=True).values('id', 'name'))
            cache.set('academic_schemes', schemes, 3600)
            
            subjects = list(Subject.objects.filter(is_active=True).values('id', 'name', 'scheme_id'))
            cache.set('academic_subjects', subjects, 3600)
            
            # Cache featured content
            featured_events = list(Event.objects.filter(
                is_featured=True, status='published'
            ).values('id', 'title', 'start_date')[:5])
            cache.set('featured_events', featured_events, 1800)
            
            featured_projects = list(Project.objects.filter(
                is_featured=True, is_published=True
            ).values('id', 'title', 'created_at')[:6])
            cache.set('featured_projects', featured_projects, 1800)
            
            # Cache statistics
            stats = {
                'total_events': Event.objects.count(),
                'total_projects': Project.objects.count(),
                'total_images': GalleryImage.objects.filter(is_public=True).count(),
                'total_albums': GalleryAlbum.objects.filter(is_public=True).count(),
            }
            cache.set('site_statistics', stats, 3600)
            
            self.stdout.write(self.style.SUCCESS('✅ Cache warmed up successfully'))
            
        except Exception as e:
            self.stdout.write(self.style.ERROR(f'❌ Cache warm-up failed: {str(e)}'))
