# Production PostgreSQL Indexing Strategy for Supabase

## Django vs Manual Database Indexing

### 1. Django Migrations (Current Approach)
✅ **Pros**: 
- Version controlled with code
- Automatically applied during deployment
- Reversible with Django migrations
- Works across development and production

❌ **Cons**: 
- Limited to Django's index syntax
- May not use all PostgreSQL-specific features
- Requires migration deployment

### 2. Manual Supabase Dashboard Indexing
✅ **Pros**: 
- Full PostgreSQL feature access
- Can use advanced index types (GIN, GIST, etc.)
- Immediate application
- Can fine-tune for specific workloads

❌ **Cons**: 
- Not version controlled
- Manual process (error-prone)
- Can be lost during database resets
- Not documented in code

## Recommended Hybrid Approach

**Best Practice**: Use Django migrations for basic indexes + Manual SQL for advanced PostgreSQL-specific optimizations.

## Current Analysis

Based on your code, you're currently in **development mode** (SQLite), so our migrations only applied to SQLite. For production, we need to ensure indexes are applied to your Supabase PostgreSQL database.

### Database Configuration Check
```python
# In settings.py - You have proper PostgreSQL config for production
if DEBUG:
    # Development: SQLite
    DATABASES = {'default': {'ENGINE': 'django.db.backends.sqlite3'}}
else:
    # Production: PostgreSQL (Supabase)
    DATABASES = {'default': {'ENGINE': 'django.db.backends.postgresql'}}
```

## Production Indexing Strategy

### Phase 1: Django Model-Level Indexes (Already Done)
These work in both SQLite and PostgreSQL:

```python
class Subject(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['scheme', 'semester']),     # Filtering
            models.Index(fields=['code']),                   # Lookups
            models.Index(fields=['department']),             # Department filter
        ]

class AcademicResource(models.Model):
    class Meta:
        indexes = [
            models.Index(fields=['category', 'subject']),    # Main filtering
            models.Index(fields=['uploaded_by']),            # User resources
            models.Index(fields=['is_approved']),            # Approval filter
            models.Index(fields=['created_at']),             # Date ordering
        ]
```

### Phase 2: Advanced PostgreSQL Indexes (Manual + Migration)
These are PostgreSQL-specific and provide major performance gains:

#### A. Composite Indexes for Complex Queries
```sql
-- Most common query pattern in academics page
CREATE INDEX CONCURRENTLY idx_resource_main_filter 
ON academics_academicresource (subject_id, category, is_approved, created_at DESC);

-- Subject filtering by scheme + semester + department
CREATE INDEX CONCURRENTLY idx_subject_scheme_sem_dept 
ON academics_subject (scheme_id, semester, department);

-- Approved resources only (much faster than full table scan)
CREATE INDEX CONCURRENTLY idx_approved_resources 
ON academics_academicresource (created_at DESC) 
WHERE is_approved = true;
```

#### B. Full-Text Search Indexes (PostgreSQL GIN)
```sql
-- Full-text search for titles and descriptions
CREATE INDEX CONCURRENTLY idx_resource_fulltext 
ON academics_academicresource 
USING gin(to_tsvector('english', title || ' ' || COALESCE(description, '')));

-- Subject name search
CREATE INDEX CONCURRENTLY idx_subject_search 
ON academics_subject 
USING gin(to_tsvector('english', name || ' ' || code));
```

#### C. Performance-Critical Indexes
```sql
-- User's uploaded resources (for profile pages)
CREATE INDEX CONCURRENTLY idx_user_resources 
ON academics_academicresource (uploaded_by_id, created_at DESC) 
WHERE is_approved = true;

-- Popular resources (for recommendations)
CREATE INDEX CONCURRENTLY idx_popular_resources 
ON academics_academicresource (like_count DESC, download_count DESC) 
WHERE is_approved = true;

-- File size filtering (for mobile optimization)
CREATE INDEX CONCURRENTLY idx_resource_size 
ON academics_academicresource (file_size) 
WHERE is_approved = true AND file_size IS NOT NULL;
```

## Implementation Strategy

### Option 1: Production-Ready Migration (Recommended)
I'll create a migration that detects PostgreSQL and applies advanced indexes:
