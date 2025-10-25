#!/bin/bash
# Production Preparation Script
# Cleans up development files and prepares for deployment

echo "🚀 Preparing EESA Backend for Production..."
echo ""

# Remove SQLite database (production uses PostgreSQL)
if [ -f "db.sqlite3" ]; then
    echo "🗑️  Removing SQLite database..."
    rm -f db.sqlite3
    rm -f db.sqlite3-journal
    rm -f db.sqlite3.backup
    echo "   ✓ SQLite files removed"
fi

# Clean media files (production uses Cloudinary)
echo ""
echo "🗑️  Cleaning media files..."
if [ -d "media" ]; then
    # Keep the directory structure but remove files
    find media -type f -delete
    echo "   ✓ Media files removed (keeping directory structure)"
fi

# Remove Python cache files
echo ""
echo "🗑️  Removing Python cache files..."
find . -type d -name "__pycache__" -exec rm -rf {} + 2>/dev/null || true
find . -type f -name "*.pyc" -delete 2>/dev/null || true
find . -type f -name "*.pyo" -delete 2>/dev/null || true
find . -type d -name "*.egg-info" -exec rm -rf {} + 2>/dev/null || true
echo "   ✓ Python cache cleaned"

# Remove logs
echo ""
echo "🗑️  Cleaning log files..."
if [ -d "logs" ]; then
    find logs -type f -name "*.log" -delete 2>/dev/null || true
    echo "   ✓ Log files removed"
fi

# Remove .DS_Store files (macOS)
echo ""
echo "🗑️  Removing macOS files..."
find . -name ".DS_Store" -delete 2>/dev/null || true
echo "   ✓ .DS_Store files removed"

# Remove backup files
echo ""
echo "🗑️  Removing backup files..."
find . -name "*.bak" -delete 2>/dev/null || true
find . -name "*.backup" -delete 2>/dev/null || true
find . -name "*.old" -delete 2>/dev/null || true
echo "   ✓ Backup files removed"

# Verify critical files exist
echo ""
echo "✅ Verifying critical files..."
critical_files=(
    "requirements.txt"
    "Procfile"
    "runtime.txt"
    "manage.py"
    ".env.production"
    "eesa_backend/settings.py"
)

for file in "${critical_files[@]}"; do
    if [ -f "$file" ]; then
        echo "   ✓ $file"
    else
        echo "   ❌ MISSING: $file"
    fi
done

# Check docs folder is intact
echo ""
echo "📚 Verifying documentation..."
if [ -d "docs" ]; then
    doc_count=$(find docs -type f | wc -l)
    echo "   ✓ docs/ folder intact ($doc_count files)"
else
    echo "   ⚠️  docs/ folder not found"
fi

echo ""
echo "======================================"
echo "✅ Production Preparation Complete!"
echo "======================================"
echo ""
echo "📝 Next Steps:"
echo "   1. Review changes: git status"
echo "   2. Test locally: python manage.py runserver"
echo "   3. Commit: git add . && git commit -m 'Prepare for production'"
echo "   4. Deploy: git push heroku main"
echo ""
echo "⚠️  Remember to set environment variables on Heroku:"
echo "   - DEBUG=False"
echo "   - SECRET_KEY"
echo "   - DATABASE_URL"
echo "   - CLOUDINARY_CLOUD_NAME"
echo "   - CLOUDINARY_API_KEY"
echo "   - CLOUDINARY_API_SECRET"
echo ""
