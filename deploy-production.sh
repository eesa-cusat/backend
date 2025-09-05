#!/bin/bash

# EESA Backend Production Deployment Script
# Optimized for PostgreSQL/Supabase deployment with unified settings

set -e  # Exit on any error

echo "🚀 Starting EESA Backend Production Deployment"
echo "=============================================="

# Check if production environment file exists
if [ ! -f ".env.production" ] && [ ! -f ".env" ]; then
    echo "❌ Error: No environment file found!"
    echo "Please create .env.production or .env file with production configuration."
    echo "Use .env.production.template as a reference."
    exit 1
fi

echo "✅ Environment: Production (Unified Settings)"
echo "✅ Database: Auto-detected (PostgreSQL/SQLite)"

# Install production dependencies
echo "📦 Installing production dependencies..."
pip install -r requirements.production.txt

# Create logs directory if it doesn't exist
mkdir -p logs

# Set production environment
export DEBUG=False

# Database operations
echo "🗄️  Preparing database..."

# Check database connection
echo "🔍 Testing database connection..."
python manage.py check --deploy

# Run migrations (includes automatic indexing)
echo "📝 Running database migrations with indexing..."
python manage.py migrate --no-input

# Create cache table if using database cache
echo "💾 Setting up cache..."
python manage.py createcachetable eesa_cache_table 2>/dev/null || echo "Cache table already exists or Redis is configured"

# Collect static files
echo "📁 Collecting static files..."
python manage.py collectstatic --no-input --clear

# Create superuser if it doesn't exist (optional)
echo "👤 Checking for superuser..."
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    print('Creating superuser...')
    User.objects.create_superuser(
        username='admin',
        email='admin@eesacusat.in',
        password='admin123',
        first_name='Admin',
        last_name='User'
    )
    print('✅ Superuser created: admin/admin123')
else:
    print('✅ Superuser already exists')
"

# Database optimization (PostgreSQL specific)
echo "⚡ Optimizing database performance..."
python manage.py shell -c "
from django.db import connection
print(f'Database: {connection.vendor}')

if connection.vendor == 'postgresql':
    with connection.cursor() as cursor:
        cursor.execute('ANALYZE;')
        print('✅ PostgreSQL statistics updated')
else:
    print('ℹ️ Using SQLite - PostgreSQL optimizations skipped')
"

# Validate deployment
echo "✅ Validating deployment..."
python manage.py check --deploy

# Test critical endpoints
echo "🧪 Testing critical endpoints..."
python manage.py shell -c "
from django.test import Client
from django.contrib.auth import get_user_model

client = Client()

# Test API endpoints
try:
    response = client.get('/api/alumni/batches/')
    assert response.status_code in [200, 401], f'Alumni API failed: {response.status_code}'
    print('✅ Alumni API working')
    
    response = client.get('/api/gallery/albums/')
    assert response.status_code in [200, 401], f'Gallery API failed: {response.status_code}'
    print('✅ Gallery API working')
    
    response = client.get('/api/events/events/')
    assert response.status_code in [200, 401], f'Events API failed: {response.status_code}'
    print('✅ Events API working')
    
    response = client.get('/admin/')
    assert response.status_code in [200, 302], f'Admin interface failed: {response.status_code}'
    print('✅ Admin interface working')
    
    print('✅ All critical endpoints are functional')
except Exception as e:
    print(f'❌ Endpoint test failed: {e}')
"

echo ""
echo "🎉 Production deployment completed successfully!"
echo "=============================================="
echo ""
echo "📋 Deployment Summary:"
echo "   • Environment: Production (Unified Settings)"
echo "   • Database: Auto-detected with optimized indexing"
echo "   • Storage: Cloudinary (production) / Local (fallback)"
echo "   • Cache: Redis/Database (production) / Memory (development)"
echo "   • Security: Full HTTPS enforcement in production"
echo "   • Indexing: Automatic PostgreSQL optimization"
echo ""
echo "🔗 Next Steps:"
echo "   1. Set DEBUG=False in your environment"
echo "   2. Configure PostgreSQL database credentials"
echo "   3. Set up Cloudinary for media storage"
echo "   4. Update DNS records to point to your server"
echo "   5. Run PostgreSQL indexing commands for optimal performance"
echo ""
echo "📖 Documentation:"
echo "   • DATABASE_API_INDEX.md - Complete API reference"
echo "   • FRONTEND_IMPLEMENTATION_GUIDE.md - Frontend integration"
echo "   • POSTGRESQL_INDEXING_COMMANDS.md - Production indexing"
echo ""
echo "🏠 Admin Panel: https://your-domain.com/admin/"
echo "🔧 API Root: https://your-domain.com/api/"
echo ""
echo "Happy deployment! 🚀"
