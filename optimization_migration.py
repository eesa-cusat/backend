# Generated optimization migration for better database performance

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0001_initial'),  # Adjust based on your latest migration
        ('events', '0001_initial'),   # Adjust based on your latest migration
        ('academics', '0001_initial'), # Adjust based on your latest migration
        ('projects', '0001_initial'),  # Adjust based on your latest migration
    ]

    operations = [
        # Add indexes to User model for better performance
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS accounts_user_email_idx ON accounts_user(email);",
            reverse_sql="DROP INDEX IF EXISTS accounts_user_email_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS accounts_user_username_idx ON accounts_user(username);",
            reverse_sql="DROP INDEX IF EXISTS accounts_user_username_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS accounts_user_is_staff_idx ON accounts_user(is_staff);",
            reverse_sql="DROP INDEX IF EXISTS accounts_user_is_staff_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS accounts_user_is_active_idx ON accounts_user(is_active);",
            reverse_sql="DROP INDEX IF EXISTS accounts_user_is_active_idx;"
        ),
        
        # Add composite indexes for common queries
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS accounts_user_is_staff_is_active_idx ON accounts_user(is_staff, is_active);",
            reverse_sql="DROP INDEX IF EXISTS accounts_user_is_staff_is_active_idx;"
        ),
        
        # TeamMember indexes
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS accounts_teammember_team_type_is_active_idx ON accounts_teammember(team_type, is_active);",
            reverse_sql="DROP INDEX IF EXISTS accounts_teammember_team_type_is_active_idx;"
        ),
        
        # Event registration indexes for performance
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS events_eventregistration_event_email_idx ON events_eventregistration(event_id, email);",
            reverse_sql="DROP INDEX IF EXISTS events_eventregistration_event_email_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS events_eventregistration_payment_status_idx ON events_eventregistration(payment_status);",
            reverse_sql="DROP INDEX IF EXISTS events_eventregistration_payment_status_idx;"
        ),
        
        # Academic resource optimization
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS academics_academicresource_category_is_approved_idx ON academics_academicresource(category, is_approved);",
            reverse_sql="DROP INDEX IF EXISTS academics_academicresource_category_is_approved_idx;"
        ),
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS academics_subject_scheme_semester_department_idx ON academics_subject(scheme_id, semester, department);",
            reverse_sql="DROP INDEX IF EXISTS academics_subject_scheme_semester_department_idx;"
        ),
        
        # Project optimization
        migrations.RunSQL(
            "CREATE INDEX IF NOT EXISTS projects_project_category_is_published_idx ON projects_project(category, is_published);",
            reverse_sql="DROP INDEX IF EXISTS projects_project_category_is_published_idx;"
        ),
    ]
