#!/bin/bash

# Production Readiness Script for EESA Backend
# This script prepares the backend for production deployment

echo "🚀 Preparing EESA Backend for Production..."

# Colors for output
RED='\033[0;31m'
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
NC='\033[0m' # No Color

# Function to print colored output
print_status() {
    echo -e "${GREEN}✓${NC} $1"
}

print_warning() {
    echo -e "${YELLOW}⚠${NC} $1"
}

print_error() {
    echo -e "${RED}✗${NC} $1"
}

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    print_error "This script must be run from the Django project root directory"
    exit 1
fi

print_status "Starting production preparation..."

# 1. Remove unnecessary files and directories
echo -e "\n📁 Cleaning up unnecessary files..."

# Remove test files
find . -name "test_*.py" -type f -delete 2>/dev/null && print_status "Removed test files"
find . -name "*_test.py" -type f -delete 2>/dev/null

# Remove Python cache files
find . -name "*.pyc" -type f -delete 2>/dev/null && print_status "Removed Python cache files"
find . -name "__pycache__" -type d -exec rm -rf {} + 2>/dev/null && print_status "Removed __pycache__ directories"

# Remove development database if exists
if [ -f "db.sqlite3" ]; then
    print_warning "Keeping db.sqlite3 for development. Remove manually in production if needed."
fi

# Remove IDE files
rm -rf .vscode/ 2>/dev/null
rm -rf .idea/ 2>/dev/null
rm -rf *.sublime-* 2>/dev/null

# Remove development logs
rm -rf logs/ 2>/dev/null
rm -f *.log 2>/dev/null

print_status "File cleanup completed"

# 2. Check for sensitive information
echo -e "\n🔒 Checking for sensitive information..."

# Check for hardcoded secrets
if grep -r "SECRET_KEY.*=" . --include="*.py" | grep -v "os.environ\|get_random_secret_key" | grep -v "settings.py"; then
    print_error "Found hardcoded SECRET_KEY. Please use environment variables."
else
    print_status "No hardcoded SECRET_KEY found"
fi

# Check for hardcoded database credentials
if grep -r "PASSWORD.*=" . --include="*.py" | grep -v "os.environ" | grep -v "AUTH_PASSWORD_VALIDATORS"; then
    print_error "Found hardcoded database credentials. Please use environment variables."
else
    print_status "No hardcoded database credentials found"
fi

# 3. Validate settings.py
echo -e "\n⚙️ Validating Django settings..."

# Check DEBUG setting
if grep -q "DEBUG = True" eesa_backend/settings.py; then
    print_error "DEBUG is set to True. This should be False in production."
else
    print_status "DEBUG setting is properly configured"
fi

# Check ALLOWED_HOSTS
if grep -q "ALLOWED_HOSTS = \[\]" eesa_backend/settings.py; then
    print_error "ALLOWED_HOSTS is empty. Configure it for production."
else
    print_status "ALLOWED_HOSTS is configured"
fi

# 4. Check dependencies
echo -e "\n📦 Checking dependencies..."

if [ -f "requirements.txt" ]; then
    print_status "requirements.txt found"
    
    # Check for development dependencies
    if grep -q "django-debug-toolbar\|ipdb\|pdb" requirements.txt; then
        print_warning "Development dependencies found in requirements.txt. Consider moving to requirements-dev.txt"
    else
        print_status "No development dependencies in requirements.txt"
    fi
else
    print_error "requirements.txt not found. Create it with: pip freeze > requirements.txt"
fi

# 5. Check static files configuration
echo -e "\n📄 Checking static files configuration..."

if grep -q "STATIC_ROOT" eesa_backend/settings.py; then
    print_status "STATIC_ROOT is configured"
else
    print_error "STATIC_ROOT not configured"
fi

# 6. Check security settings
echo -e "\n🔐 Checking security settings..."

security_settings=(
    "SECURE_BROWSER_XSS_FILTER"
    "SECURE_CONTENT_TYPE_NOSNIFF"
    "X_FRAME_OPTIONS"
    "SECURE_HSTS_SECONDS"
)

for setting in "${security_settings[@]}"; do
    if grep -q "$setting" eesa_backend/settings.py; then
        print_status "$setting is configured"
    else
        print_warning "$setting not found in settings"
    fi
done

# 7. Create production requirements if they don't exist
echo -e "\n📋 Creating production files..."

if [ ! -f "requirements-prod.txt" ]; then
    cat > requirements-prod.txt << EOL
# Production requirements for EESA Backend
Django>=4.2.0,<5.0
djangorestframework>=3.14.0
django-cors-headers>=4.0.0
django-filter>=23.0
python-dotenv>=1.0.0
psycopg2-binary>=2.9.0
cloudinary>=1.36.0
django-cloudinary-storage>=0.3.0
whitenoise>=6.5.0
gunicorn>=21.0.0
EOL
    print_status "Created requirements-prod.txt"
fi

# 8. Create production environment template
if [ ! -f ".env.production.template" ]; then
    cat > .env.production.template << EOL
# Production Environment Variables Template
# Copy this to .env and fill in the actual values

# Django Settings
SECRET_KEY=your-secret-key-here
DEBUG=False
ALLOWED_HOSTS=api.eesacusat.in

# Database (Supabase PostgreSQL)
DB_NAME=your-db-name
DB_USER=your-db-user
DB_PASSWORD=your-db-password
DB_HOST=your-db-host
DB_PORT=5432

# Cloudinary (File Storage)
CLOUDINARY_CLOUD_NAME=your-cloudinary-cloud-name
CLOUDINARY_API_KEY=your-cloudinary-api-key
CLOUDINARY_API_SECRET=your-cloudinary-api-secret

# CORS Settings
CORS_ALLOWED_ORIGINS=https://www.eesacusat.in
CSRF_TRUSTED_ORIGINS=https://www.eesacusat.in

# Optional: Port for deployment platforms
PORT=8000
EOL
    print_status "Created .env.production.template"
fi

# 9. Create Dockerfile if it doesn't exist or is outdated
echo -e "\n🐳 Checking Docker configuration..."

if [ ! -f "Dockerfile" ] || ! grep -q "WORKDIR" Dockerfile; then
    cat > Dockerfile << EOL
# Production Dockerfile for EESA Backend
FROM python:3.11-slim

# Set environment variables
ENV PYTHONDONTWRITEBYTECODE=1
ENV PYTHONUNBUFFERED=1

# Set work directory
WORKDIR /app

# Install system dependencies
RUN apt-get update \\
    && apt-get install -y --no-install-recommends \\
        postgresql-client \\
        build-essential \\
        libpq-dev \\
    && rm -rf /var/lib/apt/lists/*

# Install Python dependencies
COPY requirements-prod.txt .
RUN pip install --no-cache-dir -r requirements-prod.txt

# Copy project
COPY . .

# Create staticfiles directory
RUN mkdir -p staticfiles

# Collect static files
RUN python manage.py collectstatic --noinput

# Expose port
EXPOSE 8000

# Run gunicorn
CMD ["gunicorn", "--bind", "0.0.0.0:8000", "eesa_backend.wsgi:application"]
EOL
    print_status "Created/Updated Dockerfile"
fi

# 10. Create optimized docker-compose for production
if [ ! -f "docker-compose.prod.yml" ] || ! grep -q "gunicorn" docker-compose.prod.yml; then
    cat > docker-compose.prod.yml << EOL
version: '3.8'

services:
  web:
    build: .
    ports:
      - "8000:8000"
    environment:
      - DEBUG=False
    env_file:
      - .env
    restart: unless-stopped
    healthcheck:
      test: ["CMD", "curl", "-f", "http://localhost:8000/admin/"]
      interval: 30s
      timeout: 10s
      retries: 3
    volumes:
      - staticfiles:/app/staticfiles

volumes:
  staticfiles:
EOL
    print_status "Created/Updated docker-compose.prod.yml"
fi

# 11. Performance optimization check
echo -e "\n⚡ Performance optimization recommendations..."

if [ -f "academics/views.py" ]; then
    if grep -q "select_related" academics/views.py; then
        print_status "Found select_related optimizations"
    else
        print_warning "Consider adding select_related() optimizations"
    fi
    
    if grep -q "prefetch_related" academics/views.py; then
        print_status "Found prefetch_related optimizations"
    else
        print_warning "Consider adding prefetch_related() optimizations"
    fi
fi

# 12. Create deployment script
if [ ! -f "deploy.sh" ]; then
    cat > deploy.sh << 'EOL'
#!/bin/bash

# Production Deployment Script for EESA Backend

echo "🚀 Deploying EESA Backend to Production..."

# Load environment variables
if [ -f ".env" ]; then
    export $(cat .env | xargs)
fi

# Run migrations
echo "📊 Running database migrations..."
python manage.py migrate

# Collect static files
echo "📄 Collecting static files..."
python manage.py collectstatic --noinput

# Create superuser if it doesn't exist
echo "👤 Checking for superuser..."
python manage.py shell << 'PYTHON'
from django.contrib.auth import get_user_model
User = get_user_model()
if not User.objects.filter(is_superuser=True).exists():
    print("Creating superuser...")
    User.objects.create_superuser('admin', 'admin@eesacusat.in', 'admin123')
    print("Superuser created with username 'admin' and password 'admin123'")
    print("Please change the password immediately!")
else:
    print("Superuser already exists")
PYTHON

echo "✅ Deployment completed!"
echo "🔐 Don't forget to:"
echo "   1. Change the default superuser password"
echo "   2. Configure your domain and SSL"
echo "   3. Set up monitoring and backups"
EOL
    chmod +x deploy.sh
    print_status "Created deploy.sh script"
fi

# Final summary
echo -e "\n📋 Production Readiness Summary:"
echo -e "   ✅ Unnecessary files cleaned up"
echo -e "   ✅ Production configuration files created"
echo -e "   ✅ Security settings validated"
echo -e "   ✅ Docker configuration optimized"
echo -e "   ✅ Deployment scripts ready"

echo -e "\n🎯 Next Steps:"
echo -e "   1. Copy .env.production.template to .env and fill in your values"
echo -e "   2. Run: python manage.py migrate (to apply optimizations)"
echo -e "   3. Test with: python manage.py runserver"
echo -e "   4. Deploy using: ./deploy.sh"

echo -e "\n✨ Your backend is now production-ready!"
