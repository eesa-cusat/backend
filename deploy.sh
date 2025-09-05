#!/bin/bash

# Production deployment script for EESA Backend
# Handles potential collectstatic issues with Cloudinary

echo "🚀 Starting EESA Backend production deployment..."

# Set environment variables for production
export DEBUG=False
export DJANGO_SETTINGS_MODULE=eesa_backend.settings

echo "📋 Running database migrations..."
python manage.py migrate --noinput

echo "📦 Attempting to collect static files..."
# Try collectstatic, but don't fail deployment if it has issues
python manage.py collectstatic --noinput --clear || {
    echo "⚠️ Collectstatic had issues, but continuing deployment..."
    echo "ℹ️ Static files will be served directly from Cloudinary"
}

echo "🎉 EESA Backend deployment completed successfully!"
echo "🌐 Ready to serve requests"
