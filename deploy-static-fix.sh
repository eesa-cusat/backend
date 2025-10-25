#!/bin/bash
# Deploy to Heroku with static files fix

echo "🚀 Deploying Static Files Fix to Production"
echo "============================================"
echo ""

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo "❌ Error: Run this from the backend directory"
    exit 1
fi

# Show what changed
echo "📝 Changes being deployed:"
echo "  ✅ WhiteNoise for static files (Django admin)"
echo "  ✅ Cloudinary for media files (user uploads)"
echo "  ✅ Automatic collectstatic in Procfile"
echo "  ✅ Optimized caching configuration"
echo ""

# Confirm deployment
read -p "Deploy to Heroku? (y/n) " -n 1 -r
echo
if [[ ! $REPLY =~ ^[Yy]$ ]]; then
    echo "❌ Deployment cancelled"
    exit 1
fi

# Add and commit changes
echo ""
echo "📦 Committing changes..."
git add .
git commit -m "Fix: Production static files using WhiteNoise for Django admin

- Changed static file storage from Cloudinary to WhiteNoise
- Keep Cloudinary for media files only
- Added collectstatic to Procfile release phase
- Added WhiteNoise optimization settings
- Created static directory structure

This fixes the missing CSS/JS in production admin panel."

# Deploy to Heroku
echo ""
echo "🚀 Deploying to Heroku..."
git push heroku main

# Wait for deployment
echo ""
echo "⏳ Waiting for deployment to complete..."
sleep 3

# Check logs
echo ""
echo "📋 Checking deployment logs..."
heroku logs --tail --num 50 | grep -i "collectstatic\|static"

echo ""
echo "✅ Deployment complete!"
echo ""
echo "🔍 Next steps:"
echo "1. Visit https://api.eesacusat.in/eesa/"
echo "2. Check if admin panel has styling"
echo "3. Look for Jazzmin purple/blue theme"
echo "4. Verify responsive design works"
echo ""
echo "🐛 If styles are missing, run:"
echo "   heroku run python manage.py collectstatic --noinput --clear"
echo ""
