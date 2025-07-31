from django.core.management.base import BaseCommand
from django.conf import settings
from django.core.management import call_command
from pathlib import Path
import os

class Command(BaseCommand):
    help = 'Debug static files configuration and collection'

    def handle(self, *args, **options):
        self.stdout.write("=== STATIC FILES DEBUG ===")
        
        # Environment info
        self.stdout.write(f"DEBUG: {settings.DEBUG}")
        self.stdout.write(f"STATICFILES_STORAGE: {settings.STATICFILES_STORAGE}")
        self.stdout.write(f"STATIC_URL: {settings.STATIC_URL}")
        self.stdout.write(f"STATIC_ROOT: {settings.STATIC_ROOT}")
        
        # Cloudinary info
        if not settings.DEBUG:
            self.stdout.write(f"CLOUDINARY_CLOUD_NAME: {getattr(settings, 'CLOUDINARY_CLOUD_NAME', 'Not set')}")
            self.stdout.write(f"CLOUDINARY_API_KEY: {'Set' if getattr(settings, 'CLOUDINARY_API_KEY', None) else 'Not set'}")
            self.stdout.write(f"CLOUDINARY_API_SECRET: {'Set' if getattr(settings, 'CLOUDINARY_API_SECRET', None) else 'Not set'}")
        
        # Check static files
        static_root = Path(settings.STATIC_ROOT)
        self.stdout.write(f"STATIC_ROOT exists: {static_root.exists()}")
        
        if static_root.exists():
            file_count = sum(1 for _ in static_root.rglob('*') if _.is_file())
            self.stdout.write(f"Files in STATIC_ROOT: {file_count}")
            
            # List some files
            files = list(static_root.rglob('*'))[:10]
            for file_path in files:
                if file_path.is_file():
                    self.stdout.write(f"  - {file_path.relative_to(static_root)}")
        
        # Run collectstatic with verbosity
        self.stdout.write("\n=== RUNNING COLLECTSTATIC ===")
        try:
            call_command('collectstatic', '--noinput', '--clear', verbosity=2)
            self.stdout.write("✅ collectstatic completed")
        except Exception as e:
            self.stdout.write(f"❌ collectstatic failed: {e}")
        
        # Check results
        if static_root.exists():
            file_count = sum(1 for _ in static_root.rglob('*') if _.is_file())
            self.stdout.write(f"Files after collectstatic: {file_count}")
        
        self.stdout.write("=== DEBUG COMPLETE ===") 