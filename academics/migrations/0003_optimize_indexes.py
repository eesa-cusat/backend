# Production-optimized indexing migration for PostgreSQL (Supabase)
# This migration detects the database type and applies appropriate indexes

from django.db import migrations, connection


def apply_postgresql_indexes(apps, schema_editor):
    """Apply PostgreSQL-specific indexes for production (Supabase)"""
    if connection.vendor != 'postgresql':
        print("Skipping PostgreSQL-specific indexes (not using PostgreSQL)")
        return
    
    print("Applying PostgreSQL-specific indexes for production...")
    
    with connection.cursor() as cursor:
        # 1. Composite index for the most common query pattern (scheme + semester + department + approval)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_resource_main_filter 
            ON academics_academicresource (subject_id, category, is_approved, created_at DESC);
        """)
        
        # 2. Subject filtering optimization (scheme + semester + department)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_subject_scheme_sem_dept 
            ON academics_subject (scheme_id, semester, department);
        """)
        
        # 3. Partial index for approved resources only (90% of queries)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_approved_resources 
            ON academics_academicresource (created_at DESC, category) 
            WHERE is_approved = true;
        """)
        
        # 4. Search optimization index
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_resource_search 
            ON academics_academicresource (title, is_approved, category);
        """)
        
        # 5. User resources index (for admin and user dashboards)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_user_resources 
            ON academics_academicresource (uploaded_by_id, created_at DESC) 
            WHERE is_approved = true;
        """)
        
        # 6. Popular resources index (like + download count)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_popular_resources 
            ON academics_academicresource (like_count DESC, download_count DESC) 
            WHERE is_approved = true;
        """)
        
        # 7. Basic text search index (without GIN to avoid transaction issues)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_resource_title_search 
            ON academics_academicresource (title) 
            WHERE is_approved = true;
        """)
        
        # 8. Subject name search
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_subject_name_search 
            ON academics_subject (name, code);
        """)
        
        # 9. File size filtering (for mobile optimization)
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_resource_size 
            ON academics_academicresource (file_size, category) 
            WHERE is_approved = true AND file_size IS NOT NULL;
        """)
        
        # 10. Resource likes optimization
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_resource_likes 
            ON academics_resourcelike (resource_id, ip_address);
        """)
        
    print("✅ PostgreSQL indexes applied successfully!")


def remove_postgresql_indexes(apps, schema_editor):
    """Remove PostgreSQL-specific indexes"""
    if connection.vendor != 'postgresql':
        return
        
    with connection.cursor() as cursor:
        indexes_to_drop = [
            'idx_resource_main_filter',
            'idx_subject_scheme_sem_dept', 
            'idx_approved_resources',
            'idx_resource_search',
            'idx_user_resources',
            'idx_popular_resources',
            'idx_resource_title_search',
            'idx_subject_name_search',
            'idx_resource_size',
            'idx_resource_likes'
        ]
        
        for index_name in indexes_to_drop:
            cursor.execute(f"DROP INDEX IF EXISTS {index_name};")


def apply_sqlite_indexes(apps, schema_editor):
    """Apply basic indexes for SQLite (development)"""
    if connection.vendor != 'sqlite':
        print("Skipping SQLite indexes (not using SQLite)")
        return
        
    print("Applying SQLite-compatible indexes for development...")
    
    with connection.cursor() as cursor:
        # Basic indexes that work in SQLite
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_resource_basic_filter 
            ON academics_academicresource (subject_id, category, is_approved);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_subject_basic_filter 
            ON academics_subject (scheme_id, semester, department);
        """)
        
        cursor.execute("""
            CREATE INDEX IF NOT EXISTS idx_resource_approved 
            ON academics_academicresource (is_approved, created_at);
        """)
        
    print("✅ SQLite indexes applied successfully!")


def remove_sqlite_indexes(apps, schema_editor):
    """Remove SQLite indexes"""
    if connection.vendor != 'sqlite':
        return
        
    with connection.cursor() as cursor:
        cursor.execute("DROP INDEX IF EXISTS idx_resource_basic_filter;")
        cursor.execute("DROP INDEX IF EXISTS idx_subject_basic_filter;")
        cursor.execute("DROP INDEX IF EXISTS idx_resource_approved;")


class Migration(migrations.Migration):

    dependencies = [
        ('academics', '0002_initial'),
    ]

    operations = [
        # Apply database-specific indexes
        migrations.RunPython(
            code=apply_postgresql_indexes,
            reverse_code=remove_postgresql_indexes,
        ),
        migrations.RunPython(
            code=apply_sqlite_indexes,
            reverse_code=remove_sqlite_indexes,
        ),
    ]
