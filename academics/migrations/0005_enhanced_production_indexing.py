# Generated for enhanced production indexing (transaction-safe version)

from django.db import migrations, models

class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0004_optimize_database_indexes'),
    ]

    operations = [
        # Add text search vector field for full-text search
        migrations.AddField(
            model_name='academicresource',
            name='search_vector',
            field=models.TextField(blank=True, null=True, help_text='Generated search vector for full-text search'),
        ),
        
        # Regular B-tree indexes (transaction-safe)
        migrations.RunSQL(
            sql=[
                # Enhanced composite indexes for common query patterns
                "CREATE INDEX IF NOT EXISTS idx_academic_resource_category_subject ON academics_academicresource(category, subject_id);",
                "CREATE INDEX IF NOT EXISTS idx_academic_resource_approval_status ON academics_academicresource(is_approved, is_active, created_at DESC);",
                "CREATE INDEX IF NOT EXISTS idx_academic_resource_module_category ON academics_academicresource(module_number, category);",
                
                # Performance indexes for sorting and filtering
                "CREATE INDEX IF NOT EXISTS idx_academic_resource_popular ON academics_academicresource(download_count DESC, like_count DESC) WHERE is_approved = true AND is_active = true;",
                "CREATE INDEX IF NOT EXISTS idx_academic_resource_recent ON academics_academicresource(created_at DESC) WHERE is_approved = true AND is_active = true;",
                
                # Subject-specific optimizations
                "CREATE INDEX IF NOT EXISTS idx_subject_department_semester ON academics_subject(department, semester, scheme_id);",
                "CREATE INDEX IF NOT EXISTS idx_subject_code_scheme ON academics_subject(code, scheme_id);",
                
                # Scheme optimizations
                "CREATE INDEX IF NOT EXISTS idx_scheme_active_year ON academics_scheme(is_active, year DESC);",
                
                # Text search function and trigger for full-text search
                """
                CREATE OR REPLACE FUNCTION update_academic_search_vector()
                RETURNS TRIGGER AS $$
                BEGIN
                    NEW.search_vector := to_tsvector('english', 
                        COALESCE(NEW.title, '') || ' ' ||
                        COALESCE(NEW.description, '') || ' ' ||
                        COALESCE(NEW.category, '')
                    );
                    RETURN NEW;
                END;
                $$ LANGUAGE plpgsql;
                """,
                
                "DROP TRIGGER IF EXISTS update_academic_search_vector_trigger ON academics_academicresource;",
                
                """
                CREATE TRIGGER update_academic_search_vector_trigger
                    BEFORE INSERT OR UPDATE ON academics_academicresource
                    FOR EACH ROW EXECUTE FUNCTION update_academic_search_vector();
                """,
            ],
            reverse_sql=[
                "DROP TRIGGER IF EXISTS update_academic_search_vector_trigger ON academics_academicresource;",
                "DROP FUNCTION IF EXISTS update_academic_search_vector();",
                "DROP INDEX IF EXISTS idx_academic_resource_category_subject;",
                "DROP INDEX IF EXISTS idx_academic_resource_approval_status;",
                "DROP INDEX IF EXISTS idx_academic_resource_module_category;",
                "DROP INDEX IF EXISTS idx_academic_resource_popular;",
                "DROP INDEX IF EXISTS idx_academic_resource_recent;",
                "DROP INDEX IF EXISTS idx_subject_department_semester;",
                "DROP INDEX IF EXISTS idx_subject_code_scheme;",
                "DROP INDEX IF EXISTS idx_scheme_active_year;",
            ]
        ),
        
        # Update existing records with search vectors
        migrations.RunSQL(
            sql=[
                """
                UPDATE academics_academicresource SET search_vector = to_tsvector('english', 
                    COALESCE(title, '') || ' ' ||
                    COALESCE(description, '') || ' ' ||
                    COALESCE(category, '')
                );
                """
            ],
            reverse_sql=["UPDATE academics_academicresource SET search_vector = NULL;"]
        ),
    ]
