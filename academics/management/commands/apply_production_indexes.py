"""
Django management command to apply production-grade indexes with CONCURRENTLY
This command should be run AFTER successful deployment to apply advanced indexes
"""

from django.core.management.base import BaseCommand
from django.db import connection
from django.conf import settings


class Command(BaseCommand):
    help = 'Apply production-grade concurrent indexes for optimal performance'

    def add_arguments(self, parser):
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force apply indexes even if not in production',
        )

    def handle(self, *args, **options):
        if connection.vendor != 'postgresql':
            self.stdout.write(
                self.style.WARNING('⚠️ This command is only for PostgreSQL databases (Supabase)')
            )
            return

        if not options['force'] and settings.DEBUG:
            self.stdout.write(
                self.style.WARNING('⚠️ This command is intended for production. Use --force to run in development.')
            )
            return

        self.stdout.write(self.style.SUCCESS('🚀 Applying production-grade concurrent indexes...'))
        
        # Apply all the advanced indexes with CONCURRENTLY
        indexes = self.get_production_indexes()
        
        success_count = 0
        error_count = 0
        
        for index_name, sql in indexes.items():
            try:
                self.stdout.write(f'📝 Creating index: {index_name}...')
                
                # Execute outside of transaction for CONCURRENTLY to work
                with connection.cursor() as cursor:
                    cursor.execute(sql)
                
                self.stdout.write(
                    self.style.SUCCESS(f'✅ {index_name} created successfully')
                )
                success_count += 1
                
            except Exception as e:
                self.stdout.write(
                    self.style.ERROR(f'❌ Failed to create {index_name}: {str(e)}')
                )
                error_count += 1
        
        # Summary
        self.stdout.write('\n' + '='*60)
        self.stdout.write(self.style.SUCCESS(f'📊 INDEXING COMPLETE'))
        self.stdout.write(self.style.SUCCESS(f'✅ Successful: {success_count}'))
        if error_count > 0:
            self.stdout.write(self.style.ERROR(f'❌ Failed: {error_count}'))
        self.stdout.write('='*60)
        
        if success_count > 0:
            self.stdout.write(
                self.style.SUCCESS(
                    f'\n🎉 Production indexes applied! Your database is now optimized for high performance.'
                )
            )

    def get_production_indexes(self):
        """Return dictionary of production indexes to create"""
        return {
            # ACCOUNTS MODULE INDEXES
            'idx_accounts_user_email': """
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_accounts_user_email 
                ON accounts_user (email);
            """,
            
            'idx_accounts_user_active': """
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_accounts_user_active 
                ON accounts_user (is_active, date_joined);
            """,
            
            'idx_accounts_teammember_type_active': """
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_accounts_teammember_type_active 
                ON accounts_teammember (team_type, is_active, "order");
            """,
            
            'idx_accounts_teammember_search': """
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_accounts_teammember_search 
                ON accounts_teammember 
                USING gin(to_tsvector('english', name || ' ' || position));
            """,

            # EVENTS MODULE INDEXES
            'idx_events_event_status_featured': """
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_event_status_featured 
                ON events_event (status, is_featured, is_active);
            """,
            
            'idx_events_event_dates': """
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_event_dates 
                ON events_event (start_date, end_date);
            """,
            
            'idx_events_event_type_status': """
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_event_type_status 
                ON events_event (event_type, status, start_date DESC);
            """,
            
            'idx_events_event_search': """
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_event_search 
                ON events_event 
                USING gin(to_tsvector('english', title || ' ' || description));
            """,
            
            'idx_events_registration_event_status': """
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_registration_event_status 
                ON events_eventregistration (event_id, payment_status);
            """,

            # PROJECTS MODULE INDEXES
            'idx_projects_project_category_featured': """
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_projects_project_category_featured 
                ON projects_project (category, is_featured, is_published);
            """,
            
            'idx_projects_project_published': """
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_projects_project_published 
                ON projects_project (is_published, created_at DESC) 
                WHERE is_published = true;
            """,
            
            'idx_projects_project_search': """
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_projects_project_search 
                ON projects_project 
                USING gin(to_tsvector('english', title || ' ' || description));
            """,

            # GALLERY MODULE INDEXES
            'idx_gallery_category_active': """
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_gallery_category_active 
                ON gallery_gallerycategory (is_active, display_order);
            """,
            
            'idx_gallery_album_category_featured': """
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_gallery_album_category_featured 
                ON gallery_galleryalbum (category_id, is_featured, is_active);
            """,
            
            'idx_gallery_image_album_public': """
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_gallery_image_album_public 
                ON gallery_galleryimage (album_id, is_public, is_featured);
            """,
            
            'idx_gallery_image_search': """
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_gallery_image_search 
                ON gallery_galleryimage 
                USING gin(to_tsvector('english', title || ' ' || COALESCE(description, '')));
            """,

            # PLACEMENTS MODULE INDEXES
            'idx_placements_company_active': """
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_placements_company_active 
                ON placements_company (is_active, is_verified, created_at DESC);
            """,
            
            'idx_placements_drive_company_active': """
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_placements_drive_company_active 
                ON placements_placementdrive (company_id, is_active, drive_date DESC);
            """,
            
            'idx_placements_drive_dates': """
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_placements_drive_dates 
                ON placements_placementdrive (registration_start, registration_end, drive_date);
            """,

            # ALUMNI MODULE INDEXES
            'idx_alumni_passout_employment': """
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alumni_passout_employment 
                ON alumni_alumni (year_of_passout, employment_status, is_active);
            """,
            
            'idx_alumni_search': """
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alumni_search 
                ON alumni_alumni 
                USING gin(to_tsvector('english', full_name || ' ' || COALESCE(current_company, '')));
            """,

            # CAREERS MODULE INDEXES
            'idx_careers_job_active_posted': """
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_careers_job_active_posted 
                ON careers_jobopportunity (is_active, posted_at DESC);
            """,
            
            'idx_careers_job_search': """
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_careers_job_search 
                ON careers_jobopportunity 
                USING gin(to_tsvector('english', title || ' ' || company || ' ' || location));
            """,

            # ACADEMICS ADVANCED INDEXES
            'idx_academics_resource_fulltext': """
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_academics_resource_fulltext 
                ON academics_academicresource 
                USING gin(to_tsvector('english', title || ' ' || COALESCE(description, '')));
            """,
            
            'idx_academics_subject_search': """
                CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_academics_subject_search 
                ON academics_subject 
                USING gin(to_tsvector('english', name || ' ' || code));
            """,
        }
