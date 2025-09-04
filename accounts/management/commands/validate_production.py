from django.core.management.base import BaseCommand
from django.conf import settings
from django.db import connection
from django.contrib.auth import get_user_model
import os
import sys


class Command(BaseCommand):
    help = 'Validate production environment configuration'

    def handle(self, *args, **options):
        """Validate production environment and optimizations"""
        
        self.stdout.write(self.style.HTTP_INFO('🔍 EESA Production Environment Validation'))
        self.stdout.write(self.style.HTTP_INFO('=' * 50))
        
        errors = []
        warnings = []
        success_count = 0
        
        # Check Django settings
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('Django Configuration:'))
        
        if settings.DEBUG:
            errors.append('DEBUG is True - should be False in production')
        else:
            self.stdout.write(self.style.SUCCESS('✅ DEBUG is False'))
            success_count += 1
            
        if settings.SECRET_KEY == 'django-insecure-zpdpc&fkd@i+9%j6sqft4es&=h4p=_vl+sgwjsh5df+h$3e!of':
            warnings.append('Using default SECRET_KEY - should generate a new one')
        else:
            self.stdout.write(self.style.SUCCESS('✅ Custom SECRET_KEY configured'))
            success_count += 1
            
        # Check allowed hosts
        if '*' in settings.ALLOWED_HOSTS:
            warnings.append('ALLOWED_HOSTS contains * - should use specific domains')
        elif settings.ALLOWED_HOSTS:
            self.stdout.write(self.style.SUCCESS(f'✅ ALLOWED_HOSTS configured: {", ".join(settings.ALLOWED_HOSTS)}'))
            success_count += 1
        else:
            errors.append('ALLOWED_HOSTS not configured')
            
        # Database validation
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('Database Configuration:'))
        
        try:
            with connection.cursor() as cursor:
                cursor.execute("SELECT 1")
                self.stdout.write(self.style.SUCCESS('✅ Database connection successful'))
                success_count += 1
                
                # Check database type
                if 'postgresql' in settings.DATABASES['default']['ENGINE']:
                    self.stdout.write(self.style.SUCCESS('✅ Using PostgreSQL (recommended for production)'))
                    success_count += 1
                else:
                    warnings.append('Not using PostgreSQL - consider upgrading for production')
                    
        except Exception as e:
            errors.append(f'Database connection failed: {e}')
            
        # Check Cloudinary configuration
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('Storage Configuration:'))
        
        cloudinary_settings = [
            'CLOUDINARY_CLOUD_NAME',
            'CLOUDINARY_API_KEY', 
            'CLOUDINARY_API_SECRET'
        ]
        
        cloudinary_configured = all(os.environ.get(key) for key in cloudinary_settings)
        if cloudinary_configured:
            self.stdout.write(self.style.SUCCESS('✅ Cloudinary storage configured'))
            success_count += 1
        else:
            warnings.append('Cloudinary not fully configured - using local storage')
            
        # Check CORS configuration
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('CORS Configuration:'))
        
        if hasattr(settings, 'CORS_ALLOWED_ORIGINS') and settings.CORS_ALLOWED_ORIGINS:
            self.stdout.write(self.style.SUCCESS(f'✅ CORS origins configured: {", ".join(settings.CORS_ALLOWED_ORIGINS)}'))
            success_count += 1
        else:
            warnings.append('CORS_ALLOWED_ORIGINS not configured')
            
        # Check optimizations
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('Optimization Status:'))
        
        # Check if optimize_db command has been run
        try:
            with connection.cursor() as cursor:
                # Check for our custom indexes
                cursor.execute("""
                    SELECT COUNT(*) FROM pg_indexes 
                    WHERE indexname LIKE 'idx_%' OR indexname LIKE '%_lookup%'
                """) if 'postgresql' in settings.DATABASES['default']['ENGINE'] else cursor.execute("""
                    SELECT COUNT(*) FROM sqlite_master 
                    WHERE type='index' AND name LIKE 'idx_%'
                """)
                
                index_count = cursor.fetchone()[0]
                if index_count > 0:
                    self.stdout.write(self.style.SUCCESS(f'✅ Database optimization indexes found: {index_count}'))
                    success_count += 1
                else:
                    warnings.append('Database optimization indexes not found - run python manage.py optimize_db')
                    
        except Exception as e:
            warnings.append(f'Could not check database indexes: {e}')
            
        # Check user groups
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('User Groups:'))
        
        from django.contrib.auth.models import Group
        required_groups = ['academics_team', 'events_team', 'careers_team', 'people_team']
        existing_groups = list(Group.objects.filter(name__in=required_groups).values_list('name', flat=True))
        
        if len(existing_groups) == len(required_groups):
            self.stdout.write(self.style.SUCCESS(f'✅ All required groups configured: {", ".join(existing_groups)}'))
            success_count += 1
        else:
            missing = set(required_groups) - set(existing_groups)
            warnings.append(f'Missing user groups: {", ".join(missing)} - run python manage.py setup_groups')
            
        # Security headers check
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('Security Configuration:'))
        
        security_settings = [
            ('SECURE_SSL_REDIRECT', 'SSL redirect'),
            ('SECURE_HSTS_SECONDS', 'HSTS headers'),
            ('SECURE_CONTENT_TYPE_NOSNIFF', 'Content type sniffing protection'),
            ('X_FRAME_OPTIONS', 'Clickjacking protection'),
        ]
        
        for setting, description in security_settings:
            if hasattr(settings, setting) and getattr(settings, setting):
                self.stdout.write(self.style.SUCCESS(f'✅ {description} enabled'))
                success_count += 1
            else:
                warnings.append(f'{description} not configured')
                
        # Final summary
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('Validation Summary:'))
        self.stdout.write(f'✅ Successful checks: {success_count}')
        
        if warnings:
            self.stdout.write(f'⚠️  Warnings: {len(warnings)}')
            for warning in warnings:
                self.stdout.write(self.style.WARNING(f'   • {warning}'))
                
        if errors:
            self.stdout.write(f'❌ Errors: {len(errors)}')
            for error in errors:
                self.stdout.write(self.style.ERROR(f'   • {error}'))
            self.stdout.write('')
            self.stdout.write(self.style.ERROR('❌ Production environment has critical issues that need fixing'))
            sys.exit(1)
        else:
            self.stdout.write('')
            if warnings:
                self.stdout.write(self.style.WARNING('⚠️  Production environment is mostly ready but has some warnings'))
            else:
                self.stdout.write(self.style.SUCCESS('✅ Production environment is fully optimized and ready!'))
                
        self.stdout.write('')
        self.stdout.write(self.style.HTTP_INFO('🚀 EESA Backend is production-ready!'))
