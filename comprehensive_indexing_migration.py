"""
Production Database Optimization Migration
Creates comprehensive indexes across all modules for maximum performance
"""

from django.db import migrations, connection


class Migration(migrations.Migration):
    
    dependencies = [
        ('academics', '0002_initial'),
        ('events', '0001_initial'),
        ('projects', '0001_initial'),
        ('gallery', '0001_initial'),
        ('placements', '0001_initial'),
        ('alumni', '0001_initial'),
        ('careers', '0001_initial'),
        ('accounts', '0001_initial'),
    ]

    def is_postgresql(self):
        """Check if we're using PostgreSQL (production)"""
        return connection.vendor == 'postgresql'

    def create_indexes_postgresql(self, schema_editor):
        """Create PostgreSQL-specific indexes for production"""
        if not self.is_postgresql():
            return

        # Execute all production indexes
        indexes = [
            # ACCOUNTS MODULE INDEXES
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_accounts_user_email ON accounts_user (email);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_accounts_user_groups ON accounts_user_groups (user_id, group_id);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_accounts_user_active ON accounts_user (is_active, date_joined);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_accounts_teammember_type_active ON accounts_teammember (team_type, is_active, \"order\");",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_accounts_teammember_search ON accounts_teammember USING gin(to_tsvector('english', name || ' ' || position));",

            # EVENTS MODULE INDEXES
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_event_status_featured ON events_event (status, is_featured, is_active);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_event_dates ON events_event (start_date, end_date);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_event_type_status ON events_event (event_type, status, start_date DESC);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_event_registration ON events_event (registration_required, registration_deadline) WHERE status = 'published';",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_event_search ON events_event USING gin(to_tsvector('english', title || ' ' || description));",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_registration_event_status ON events_eventregistration (event_id, payment_status);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_registration_email ON events_eventregistration (email, registered_at DESC);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_registration_payment ON events_eventregistration (payment_status, payment_date) WHERE payment_status != 'pending';",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_notification_active ON events_notification (is_active, is_marquee, priority, created_at DESC);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_events_notification_dates ON events_notification (start_date, end_date) WHERE is_active = true;",

            # PROJECTS MODULE INDEXES
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_projects_project_category_featured ON projects_project (category, is_featured, is_published);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_projects_project_published ON projects_project (is_published, created_at DESC) WHERE is_published = true;",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_projects_project_creator ON projects_project (created_by_id, created_at DESC);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_projects_project_search ON projects_project USING gin(to_tsvector('english', title || ' ' || description || ' ' || COALESCE(abstract, '')));",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_projects_image_project_featured ON projects_projectimage (project_id, is_featured, created_at);",

            # GALLERY MODULE INDEXES
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_gallery_category_active ON gallery_gallerycategory (is_active, display_order);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_gallery_album_category_featured ON gallery_galleryalbum (category_id, is_featured, is_active);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_gallery_album_public ON gallery_galleryalbum (is_public, event_date DESC) WHERE is_active = true;",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_gallery_image_album_public ON gallery_galleryimage (album_id, is_public, is_featured);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_gallery_image_search ON gallery_galleryimage USING gin(to_tsvector('english', title || ' ' || COALESCE(description, '') || ' ' || COALESCE(tags, '')));",

            # PLACEMENTS MODULE INDEXES
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_placements_company_active ON placements_company (is_active, is_verified, created_at DESC);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_placements_company_search ON placements_company USING gin(to_tsvector('english', name || ' ' || COALESCE(industry, '') || ' ' || COALESCE(location, '')));",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_placements_drive_company_active ON placements_placementdrive (company_id, is_active, drive_date DESC);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_placements_drive_dates ON placements_placementdrive (registration_start, registration_end, drive_date);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_placements_drive_featured ON placements_placementdrive (is_featured, is_active, drive_date DESC);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_placements_drive_search ON placements_placementdrive USING gin(to_tsvector('english', title || ' ' || description));",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_placements_application_drive_status ON placements_placementapplication (drive_id, status, applied_at DESC);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_placements_application_student ON placements_placementapplication (student_id, applied_at DESC);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_placements_placed_company_year ON placements_placedstudent (company_id, batch_year, package_lpa DESC);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_placements_placed_package ON placements_placedstudent (package_lpa DESC, offer_date DESC) WHERE is_verified = true AND is_active = true;",

            # ALUMNI MODULE INDEXES
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alumni_passout_employment ON alumni_alumni (year_of_passout, employment_status, is_active);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alumni_company_location ON alumni_alumni (current_company, current_location) WHERE current_company IS NOT NULL;",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alumni_mentor_contact ON alumni_alumni (willing_to_mentor, allow_contact_from_juniors) WHERE is_active = true;",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alumni_search ON alumni_alumni USING gin(to_tsvector('english', full_name || ' ' || COALESCE(current_company, '') || ' ' || COALESCE(job_title, '')));",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_alumni_batch_scheme ON alumni_alumni (year_of_passout, scheme, year_of_joining);",

            # CAREERS MODULE INDEXES
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_careers_job_active_posted ON careers_jobopportunity (is_active, posted_at DESC);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_careers_job_type_level ON careers_jobopportunity (job_type, experience_level, posted_at DESC) WHERE is_active = true;",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_careers_job_deadline ON careers_jobopportunity (application_deadline) WHERE application_deadline IS NOT NULL AND is_active = true;",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_careers_job_search ON careers_jobopportunity USING gin(to_tsvector('english', title || ' ' || company || ' ' || location || ' ' || skills));",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_careers_internship_active ON careers_internshipopportunity (is_active, posted_at DESC);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_careers_internship_type_remote ON careers_internshipopportunity (internship_type, is_remote, start_date) WHERE is_active = true;",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_careers_internship_search ON careers_internshipopportunity USING gin(to_tsvector('english', title || ' ' || company || ' ' || location || ' ' || skills));",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_careers_certificate_active ON careers_certificateopportunity (is_active, posted_at DESC);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_careers_certificate_free_aid ON careers_certificateopportunity (is_free, financial_aid_available, validity_till) WHERE is_active = true;",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_careers_certificate_provider ON careers_certificateopportunity (provider, certificate_type, posted_at DESC);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_careers_certificate_search ON careers_certificateopportunity USING gin(to_tsvector('english', title || ' ' || provider || ' ' || skills_covered));",

            # FOREIGN KEY OPTIMIZATION INDEXES
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fk_events_speaker_event ON events_eventspeaker (event_id, \"order\");",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fk_events_schedule_event ON events_eventschedule (event_id, start_time);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fk_projects_team_project ON projects_teammember (project_id, name);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_fk_gallery_image_album ON gallery_galleryimage (album_id, display_order);",

            # PERFORMANCE MONITORING INDEXES
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_analytics_events_monthly ON events_event (date_trunc('month', start_date), status);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_analytics_registrations_monthly ON events_eventregistration (date_trunc('month', registered_at), payment_status);",
            "CREATE INDEX CONCURRENTLY IF NOT EXISTS idx_analytics_placements_yearly ON placements_placedstudent (batch_year, package_lpa, category);"
        ]

        # Execute each index creation
        for index_sql in indexes:
            try:
                schema_editor.execute(index_sql)
                print(f"✅ Created index: {index_sql.split('idx_')[1].split(' ')[0] if 'idx_' in index_sql else 'unknown'}")
            except Exception as e:
                print(f"⚠️ Index creation failed: {str(e)}")

    def create_indexes_sqlite(self, schema_editor):
        """Create basic indexes for SQLite (development)"""
        if self.is_postgresql():
            return

        # Basic indexes for development (SQLite compatible)
        basic_indexes = [
            "CREATE INDEX IF NOT EXISTS idx_accounts_user_email ON accounts_user (email);",
            "CREATE INDEX IF NOT EXISTS idx_events_event_status ON events_event (status, is_active);",
            "CREATE INDEX IF NOT EXISTS idx_events_event_dates ON events_event (start_date);",
            "CREATE INDEX IF NOT EXISTS idx_projects_project_published ON projects_project (is_published, created_at);",
            "CREATE INDEX IF NOT EXISTS idx_gallery_album_public ON gallery_galleryalbum (is_public, is_active);",
            "CREATE INDEX IF NOT EXISTS idx_gallery_image_public ON gallery_galleryimage (is_public);",
            "CREATE INDEX IF NOT EXISTS idx_placements_drive_active ON placements_placementdrive (is_active, drive_date);",
            "CREATE INDEX IF NOT EXISTS idx_alumni_active ON alumni_alumni (is_active, year_of_passout);",
            "CREATE INDEX IF NOT EXISTS idx_careers_job_active ON careers_jobopportunity (is_active, posted_at);"
        ]

        for index_sql in basic_indexes:
            try:
                schema_editor.execute(index_sql)
                print(f"✅ Created basic index for development")
            except Exception as e:
                print(f"⚠️ Basic index creation failed: {str(e)}")

    operations = [
        migrations.RunPython(
            code=lambda apps, schema_editor: Migration().create_indexes_postgresql(schema_editor),
            reverse_code=migrations.RunPython.noop,
            hints={'target_db': 'default'}
        ),
        migrations.RunPython(
            code=lambda apps, schema_editor: Migration().create_indexes_sqlite(schema_editor),
            reverse_code=migrations.RunPython.noop,
            hints={'target_db': 'default'}
        ),
    ]
