#!/bin/bash

# EESA Backend - Heroku Deployment Script
# This script automates the Heroku deployment process
# Run from: /Users/afsalkalladi/Pictures/both/backend

set -e  # Exit on any error

echo "🚀 EESA Backend - Heroku Deployment Wizard"
echo "=========================================="
echo ""

# Color codes
GREEN='\033[0;32m'
YELLOW='\033[1;33m'
RED='\033[0;31m'
NC='\033[0m' # No Color

# Check if we're in the right directory
if [ ! -f "manage.py" ]; then
    echo -e "${RED}❌ Error: Please run this script from the backend directory${NC}"
    exit 1
fi

# Check if Heroku CLI is installed
if ! command -v heroku &> /dev/null; then
    echo -e "${RED}❌ Heroku CLI not found. Installing...${NC}"
    echo "Run: brew install heroku"
    exit 1
fi

echo -e "${GREEN}✅ Heroku CLI found${NC}"

# Check if logged in to Heroku
if ! heroku auth:whoami &> /dev/null; then
    echo -e "${YELLOW}⚠️  Not logged in to Heroku${NC}"
    echo "Please login:"
    heroku login
fi

echo -e "${GREEN}✅ Logged in to Heroku as $(heroku auth:whoami)${NC}"
echo ""

# Prompt for app name
echo "📝 Step 1: App Configuration"
echo "----------------------------"
read -p "Enter Heroku app name (e.g., eesa-backend): " APP_NAME

if [ -z "$APP_NAME" ]; then
    echo -e "${RED}❌ App name is required${NC}"
    exit 1
fi

# Check if app already exists
if heroku apps:info --app $APP_NAME &> /dev/null; then
    echo -e "${YELLOW}⚠️  App '$APP_NAME' already exists${NC}"
    read -p "Use existing app? (y/n): " USE_EXISTING
    if [ "$USE_EXISTING" != "y" ]; then
        exit 1
    fi
else
    echo "Creating new Heroku app: $APP_NAME"
    heroku create $APP_NAME
fi

echo -e "${GREEN}✅ App ready: $APP_NAME${NC}"
echo ""

# Add PostgreSQL
echo "🗄️  Step 2: Database Setup"
echo "-------------------------"

# Check if PostgreSQL addon exists
if heroku addons --app $APP_NAME | grep -q "heroku-postgresql"; then
    echo -e "${YELLOW}⚠️  PostgreSQL addon already exists${NC}"
else
    echo "Adding PostgreSQL addon..."
    read -p "Choose plan (1=essential-0 \$5/month, 2=mini free but limited): " DB_PLAN
    
    if [ "$DB_PLAN" == "1" ]; then
        heroku addons:create heroku-postgresql:essential-0 --app $APP_NAME
    else
        heroku addons:create heroku-postgresql:mini --app $APP_NAME
    fi
    
    echo "Waiting for database to provision..."
    sleep 5
fi

echo -e "${GREEN}✅ Database ready${NC}"
echo ""

# Configure environment variables
echo "🔧 Step 3: Environment Variables"
echo "--------------------------------"

# Generate SECRET_KEY
echo "Generating SECRET_KEY..."
SECRET_KEY=$(python -c 'from django.core.management.utils import get_random_secret_key; print(get_random_secret_key())')
heroku config:set SECRET_KEY="$SECRET_KEY" --app $APP_NAME

# Set core Django settings
heroku config:set DEBUG=False --app $APP_NAME
heroku config:set DJANGO_SETTINGS_MODULE=eesa_backend.settings --app $APP_NAME
heroku config:set ALLOWED_HOSTS=".herokuapp.com,eesacusat.in,www.eesacusat.in" --app $APP_NAME
heroku config:set DISABLE_COLLECTSTATIC=1 --app $APP_NAME

echo -e "${GREEN}✅ Core settings configured${NC}"

# Cloudinary setup
echo ""
echo "☁️  Cloudinary Configuration"
echo "---------------------------"
echo "Get your credentials from: https://cloudinary.com/console"
echo ""

read -p "Cloudinary Cloud Name: " CLOUDINARY_NAME
read -p "Cloudinary API Key: " CLOUDINARY_KEY
read -sp "Cloudinary API Secret: " CLOUDINARY_SECRET
echo ""

if [ -n "$CLOUDINARY_NAME" ] && [ -n "$CLOUDINARY_KEY" ] && [ -n "$CLOUDINARY_SECRET" ]; then
    heroku config:set CLOUDINARY_CLOUD_NAME="$CLOUDINARY_NAME" --app $APP_NAME
    heroku config:set CLOUDINARY_API_KEY="$CLOUDINARY_KEY" --app $APP_NAME
    heroku config:set CLOUDINARY_API_SECRET="$CLOUDINARY_SECRET" --app $APP_NAME
    echo -e "${GREEN}✅ Cloudinary configured${NC}"
else
    echo -e "${RED}⚠️  Cloudinary credentials incomplete. You can set them later with:${NC}"
    echo "   heroku config:set CLOUDINARY_CLOUD_NAME=your-name --app $APP_NAME"
    echo "   heroku config:set CLOUDINARY_API_KEY=your-key --app $APP_NAME"
    echo "   heroku config:set CLOUDINARY_API_SECRET=your-secret --app $APP_NAME"
fi

# CORS configuration
echo ""
read -p "Enter your frontend domain (e.g., https://eesacusat.in): " FRONTEND_URL

if [ -n "$FRONTEND_URL" ]; then
    heroku config:set CORS_ALLOWED_ORIGINS="$FRONTEND_URL" --app $APP_NAME
    heroku config:set CSRF_TRUSTED_ORIGINS="$FRONTEND_URL" --app $APP_NAME
    echo -e "${GREEN}✅ CORS configured${NC}"
fi

# Optional: Redis
echo ""
read -p "Add Redis cache? (recommended for production) (y/n): " ADD_REDIS

if [ "$ADD_REDIS" == "y" ]; then
    if heroku addons --app $APP_NAME | grep -q "heroku-redis"; then
        echo -e "${YELLOW}⚠️  Redis addon already exists${NC}"
    else
        echo "Adding Redis addon (mini plan - free)..."
        heroku addons:create heroku-redis:mini --app $APP_NAME
        echo -e "${GREEN}✅ Redis configured${NC}"
    fi
fi

echo ""
echo -e "${GREEN}✅ All environment variables configured${NC}"
echo ""

# Deploy
echo "🚀 Step 4: Deployment"
echo "--------------------"
echo "Current git status:"
git status --short

echo ""
read -p "Deploy to Heroku now? (y/n): " DEPLOY_NOW

if [ "$DEPLOY_NOW" == "y" ]; then
    # Check if there are uncommitted changes
    if [ -n "$(git status --porcelain)" ]; then
        echo "Uncommitted changes detected. Committing..."
        git add .
        read -p "Commit message (default: Configure for Heroku): " COMMIT_MSG
        COMMIT_MSG=${COMMIT_MSG:-"Configure for Heroku deployment"}
        git commit -m "$COMMIT_MSG"
    fi
    
    echo "Pushing to Heroku..."
    git push heroku main || git push heroku master:main || {
        echo -e "${RED}❌ Failed to push to Heroku${NC}"
        echo "Try manually: git push heroku your-branch:main"
        exit 1
    }
    
    echo -e "${GREEN}✅ Deployment complete${NC}"
    echo ""
    
    # Create superuser
    echo "👤 Step 5: Create Superuser"
    echo "---------------------------"
    read -p "Create superuser now? (y/n): " CREATE_USER
    
    if [ "$CREATE_USER" == "y" ]; then
        heroku run python manage.py createsuperuser --app $APP_NAME
    fi
    
    # Open app
    echo ""
    echo "🎉 Deployment Complete!"
    echo "======================"
    echo ""
    echo "App URL: https://${APP_NAME}.herokuapp.com"
    echo ""
    
    read -p "Open app in browser? (y/n): " OPEN_APP
    if [ "$OPEN_APP" == "y" ]; then
        heroku open --app $APP_NAME
    fi
    
    # Show logs
    echo ""
    read -p "View logs? (y/n): " VIEW_LOGS
    if [ "$VIEW_LOGS" == "y" ]; then
        heroku logs --tail --app $APP_NAME
    fi
else
    echo "Deployment skipped. You can deploy later with:"
    echo "  git push heroku main"
fi

echo ""
echo "📋 Next Steps:"
echo "-------------"
echo "1. Test your app: https://${APP_NAME}.herokuapp.com"
echo "2. Access admin: https://${APP_NAME}.herokuapp.com/eesa/"
echo "3. Test APIs: https://${APP_NAME}.herokuapp.com/api/"
echo "4. View logs: heroku logs --tail --app $APP_NAME"
echo "5. Update frontend env: NEXT_PUBLIC_API_BASE_URL=https://${APP_NAME}.herokuapp.com/api"
echo ""
echo "📚 Documentation:"
echo "- HEROKU_DEPLOYMENT_COMPLETE_GUIDE.md - Full deployment guide"
echo "- HEROKU_MIGRATION_CHECKLIST.md - Quick reference"
echo "- HEROKU_MIGRATION_SUMMARY.md - Changes made"
echo ""
echo "🎉 Happy deploying!"
