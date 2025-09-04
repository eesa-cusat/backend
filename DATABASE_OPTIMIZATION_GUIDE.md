# Database Optimization Guide for EESA Backend

## Current Database Status
- **Development**: SQLite3
- **Production**: PostgreSQL (Supabase)
- **Storage**: Cloudinary for files
- **Hosting**: Render

## 1. Database Indexing Strategy

### Current Indexes in Models

#### Subject Model
```python
class Meta:
    indexes = [
        models.Index(fields=['scheme', 'semester']),  # For filtering by scheme and semester
        models.Index(fields=['code']),                # For subject code lookups
        models.Index(fields=['department']),          # For department filtering
    ]
```

#### AcademicResource Model
```python
class Meta:
    indexes = [
        models.Index(fields=['category', 'subject']),  # For filtering by category and subject
        models.Index(fields=['uploaded_by']),          # For user's uploads
        models.Index(fields=['is_approved']),          # For filtering approved/unapproved
        models.Index(fields=['created_at']),           # For ordering by date
    ]
```

#### ResourceLike Model
```python
class Meta:
    indexes = [
        models.Index(fields=['resource', 'ip_address']),  # For like checking
        models.Index(fields=['created_at']),              # For analytics
    ]
```

### Additional Recommended Indexes

#### 1. Composite Indexes for Complex Queries
```python
# For academics page filtering (scheme + semester + department)
models.Index(fields=['subject__scheme', 'subject__semester', 'subject__department'])

# For approved resources by category and date
models.Index(fields=['is_approved', 'category', '-created_at'])

# For search functionality
models.Index(fields=['title', 'is_approved'])
```

#### 2. Database-Level Indexes (PostgreSQL Specific)
```sql
-- Full-text search indexes for better search performance
CREATE INDEX idx_academic_resource_search ON academics_academicresource 
USING gin(to_tsvector('english', title || ' ' || description));

-- Partial indexes for approved resources only
CREATE INDEX idx_approved_resources ON academics_academicresource (created_at DESC) 
WHERE is_approved = true;

-- Composite index for the most common query pattern
CREATE INDEX idx_resource_filter ON academics_academicresource 
(subject_id, category, is_approved, created_at DESC);
```

## 2. Query Optimization Strategies

### Use select_related() for Foreign Keys
```python
# Good: Reduces database queries
resources = AcademicResource.objects.select_related(
    'subject',
    'subject__scheme',
    'uploaded_by'
)

# Bad: Causes N+1 queries
resources = AcademicResource.objects.all()
for resource in resources:
    print(resource.subject.name)  # Additional query for each resource
```

### Use prefetch_related() for Reverse Foreign Keys
```python
# Good: Efficient for many-to-many or reverse FK relationships
resources = AcademicResource.objects.prefetch_related('likes')

# Also good for reducing queries when accessing related objects
subjects = Subject.objects.prefetch_related('resources')
```

### Use only() and defer() for Large Models
```python
# Only load specific fields when you don't need all data
resources = AcademicResource.objects.only(
    'id', 'title', 'category', 'created_at'
)

# Defer large fields when not immediately needed
resources = AcademicResource.objects.defer('description', 'file')
```

## 3. Caching Strategy

### Model-Level Caching
```python
from django.core.cache import cache

def get_schemes():
    cache_key = 'all_schemes_v1'
    schemes = cache.get(cache_key)
    if not schemes:
        schemes = list(Scheme.objects.filter(is_active=True).values())
        cache.set(cache_key, schemes, 3600)  # Cache for 1 hour
    return schemes
```

### View-Level Caching
```python
from django.views.decorators.cache import cache_page

@cache_page(60 * 15)  # Cache for 15 minutes
@api_view(['GET'])
def academic_categories_list(request):
    # This view will be cached
    pass
```

### Template Fragment Caching (if using templates)
```python
{% load cache %}
{% cache 500 schemes_list %}
    <!-- Expensive template rendering -->
{% endcache %}
```

## 4. Database Connection Optimization

### Connection Pooling (for Production)
```python
# In settings.py for PostgreSQL
DATABASES = {
    'default': {
        'ENGINE': 'django.db.backends.postgresql',
        'NAME': os.environ.get('DB_NAME'),
        'USER': os.environ.get('DB_USER'),
        'PASSWORD': os.environ.get('DB_PASSWORD'),
        'HOST': os.environ.get('DB_HOST'),
        'PORT': os.environ.get('DB_PORT', '5432'),
        'OPTIONS': {
            'MAX_CONNS': 20,
            'MIN_CONNS': 5,
        },
        'CONN_MAX_AGE': 600,  # Keep connections alive for 10 minutes
    }
}
```

## 5. File Storage Optimization

### Cloudinary Configuration
```python
# Optimize Cloudinary settings
CLOUDINARY_STORAGE = {
    'CLOUD_NAME': os.environ.get('CLOUDINARY_CLOUD_NAME'),
    'API_KEY': os.environ.get('CLOUDINARY_API_KEY'),
    'API_SECRET': os.environ.get('CLOUDINARY_API_SECRET'),
    'SECURE': True,
    'MEDIA_TAG': 'media',
    'INVALID_VIDEO_ERROR_MESSAGE': 'Please upload a valid video file.',
    'EXCLUDE_DELETE_ORPHANED_MEDIA_PATHS': (),
    'STATIC_TAG': 'static',
    'STATICFILES_MANIFEST_ROOT': os.path.join(BASE_DIR, 'manifest'),
    'STATIC_USE_CLOUDINARY': True,
}
```

## 6. Monitoring and Performance

### Database Query Monitoring
```python
# Add to settings.py for development
if DEBUG:
    LOGGING = {
        'version': 1,
        'disable_existing_loggers': False,
        'handlers': {
            'console': {
                'class': 'logging.StreamHandler',
            },
        },
        'loggers': {
            'django.db.backends': {
                'handlers': ['console'],
                'level': 'DEBUG',
            },
        },
    }
```

### Performance Monitoring Tools
1. **Django Debug Toolbar** (Development)
2. **django-extensions** for `runserver_plus`
3. **Sentry** for production error tracking
4. **New Relic** or **DataDog** for APM

## 7. Production Optimization Checklist

### Database Settings
- [ ] Enable connection pooling
- [ ] Set appropriate `CONN_MAX_AGE`
- [ ] Configure database connection limits
- [ ] Enable query optimization in PostgreSQL

### Caching
- [ ] Implement Redis for production caching
- [ ] Cache static data (schemes, categories, departments)
- [ ] Cache expensive queries
- [ ] Implement cache invalidation strategy

### File Handling
- [ ] Optimize Cloudinary transformations
- [ ] Implement progressive loading for images
- [ ] Use appropriate file formats and compression
- [ ] Enable CDN for static files

### Security & Performance
- [ ] Enable GZIP compression
- [ ] Set up proper HTTP headers
- [ ] Implement rate limiting
- [ ] Enable database query optimization
- [ ] Set up monitoring and alerting

## 8. Migration Commands for Indexing

```bash
# Create and run migrations for new indexes
python manage.py makemigrations academics
python manage.py migrate

# For manual index creation in PostgreSQL
python manage.py dbshell
# Then run the SQL commands from section 1.2
```

## 9. Performance Testing

### Load Testing Commands
```bash
# Install load testing tools
pip install locust

# Create locustfile.py for testing
# Run load tests
locust -f locustfile.py --host=https://api.eesacusat.in
```

### Database Performance Analysis
```sql
-- PostgreSQL: Check slow queries
SELECT query, mean_time, calls, total_time
FROM pg_stat_statements
ORDER BY mean_time DESC
LIMIT 10;

-- Check index usage
SELECT schemaname, tablename, attname, n_distinct, correlation
FROM pg_stats
WHERE tablename = 'academics_academicresource';
```

## 10. Recommended Next Steps

1. **Immediate (High Priority)**:
   - Implement the batch endpoint
   - Add composite indexes for common queries
   - Enable query caching for static data

2. **Short Term (Medium Priority)**:
   - Set up Redis for production caching
   - Implement database connection pooling
   - Add monitoring and logging

3. **Long Term (Low Priority)**:
   - Implement full-text search with PostgreSQL
   - Set up read replicas for heavy read workloads
   - Consider database sharding if data grows significantly

This guide provides a comprehensive approach to optimizing your Django backend for production use with Supabase, Cloudinary, and Render.
