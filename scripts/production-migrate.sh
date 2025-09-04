#!/bin/bash

# EESA Production Migration Script
# Ensures all optimizations are applied to production

echo "🚀 EESA Production Migration & Optimization"
echo "============================================"

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo "❌ Error: Please run this script from the backend directory"
    exit 1
fi

# Check if virtual environment exists
if [ ! -d ".venv" ]; then
    echo "❌ Error: Virtual environment not found at .venv"
    echo "   Create it with: python -m venv .venv"
    exit 1
fi

# Activate virtual environment
echo "🔧 Activating virtual environment..."
source .venv/bin/activate

# Check if .env file exists
if [ ! -f ".env" ]; then
    echo "⚠️  Warning: .env file not found"
    echo "   Copy .env.production to .env for production deployment"
    if [ -f ".env.production" ]; then
        echo "   Using .env.production for this migration..."
        cp .env.production .env
    else
        echo "❌ Error: No environment configuration found"
        exit 1
    fi
fi

echo ""
echo "📋 Pre-Migration Checks:"

# Check Django installation
python -c "import django; print(f'✅ Django {django.get_version()} installed')" || {
    echo "❌ Django not installed"
    echo "   Install with: pip install -r requirements.txt"
    exit 1
}

# Check database connection
echo "🗄️  Testing database connection..."
python manage.py check --database default || {
    echo "❌ Database connection failed"
    echo "   Check your database settings in .env"
    exit 1
}

echo "✅ Database connection successful"

echo ""
echo "🔄 Running Migrations:"

# Run Django migrations
echo "• Applying Django migrations..."
python manage.py migrate

# Create superuser if none exists (non-interactive)
echo ""
echo "👤 User Management:"
python manage.py shell -c "
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    print('⚠️  No superuser found. You should create one after deployment.')
else:
    superuser_count = User.objects.filter(is_superuser=True).count()
    print(f'✅ {superuser_count} superuser(s) found')
"

# Setup user groups
echo "🔐 Setting up user groups..."
python manage.py setup_groups

# Apply database optimizations
echo ""
echo "⚡ Applying Database Optimizations:"
python manage.py optimize_db

# Collect static files
echo ""
echo "📁 Static Files:"
echo "• Collecting static files..."
python manage.py collectstatic --noinput

# Run system checks
echo ""
echo "🔍 Production Readiness Checks:"
python manage.py check --deploy

echo ""
echo "📊 Final Statistics:"

# Database stats
python manage.py shell -c "
from django.db import connection
from django.contrib.auth import get_user_model
from academics.models import AcademicResource
from events.models import Event

User = get_user_model()

print(f'👥 Users: {User.objects.count()}')
print(f'📚 Academic Resources: {AcademicResource.objects.count()}')
print(f'📅 Events: {Event.objects.count()}')

# Check groups
from django.contrib.auth.models import Group
groups = Group.objects.all()
print(f'🔐 User Groups: {groups.count()}')
for group in groups:
    user_count = group.user_set.count()
    print(f'   • {group.name}: {user_count} users')
"

echo ""
echo "✅ Production Migration Complete!"
echo ""
echo "🔧 Next Steps:"
echo "1. Verify your domain settings in .env match your deployment"
echo "2. Test API endpoints: https://api.eesacusat.in/"
echo "3. Test admin panel: https://api.eesacusat.in/eesa/"
echo "4. Monitor application logs"
echo "5. Set up health monitoring"
echo ""
echo "🚀 Your EESA backend is production-ready with all optimizations applied!"

# Deactivate virtual environment
deactivate
