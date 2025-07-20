# 🎓 **EESA College Portal Backend**

A comprehensive Django backend for the EESA College Portal with academic resources, user management, and admin panel.

## 🚀 **Quick Start**

### **Local Development**
```bash
# Clone the repository
git clone <your-repo-url>
cd backend

# Create virtual environment
python -m venv .venv
source .venv/bin/activate  # On Windows: .venv\Scripts\activate

# Install dependencies
pip install -r requirements.txt

# Run migrations
python manage.py migrate

# Create superuser
python manage.py createsuperuser

# Start development server
python manage.py runserver
```

### **Docker Development**
```bash
# Start with Docker Compose
docker-compose up --build

# Access at http://localhost:8000
# Admin panel at http://localhost:8000/eesa/
```

## 🏗️ **Project Structure**

```
backend/
├── academics/          # Academic resources and notes
├── accounts/           # User management and authentication
├── alumni/             # Alumni information
├── careers/            # Career opportunities
├── events/             # College events
├── gallery/            # Image gallery
├── placements/         # Placement information
├── projects/           # Student projects
├── eesa_backend/       # Main Django settings
├── Dockerfile          # Production Docker configuration
├── docker-compose.yml  # Local development setup
├── render.yaml         # Render deployment configuration
└── requirements.txt    # Python dependencies
```

## 🔧 **Features**

### **Academic Resources**
- ✅ Upload and manage academic notes, PYQs, textbooks
- ✅ Categorize by scheme, subject, and resource type
- ✅ Verification system for academic content
- ✅ Admin panel for content management

### **User Management**
- ✅ Custom User model with groups-based permissions
- ✅ Admin panel for user management
- ✅ Role-based access control

### **File Storage**
- ✅ Cloudinary integration for production
- ✅ Local file storage for development
- ✅ Image optimization and CDN

### **API Endpoints**
- ✅ RESTful API with Django REST Framework
- ✅ JWT authentication
- ✅ CORS configuration for frontend integration

## 🚀 **Deployment**

### **Render.com (Recommended)**
```bash
# Just push to git - automatic deployment
git add .
git commit -m "Deploy latest changes"
git push origin main
```

### **Environment Variables Setup**
```env
# Database (PostgreSQL)
DB_HOST=your-database-host
DB_NAME=your-database-name
DB_PASSWORD=your-database-password
DB_PORT=5432
DB_USER=your-database-user

# Security
DEBUG=False
SECRET_KEY=your-secret-key
ALLOWED_HOSTS=localhost,127.0.0.1,0.0.0.0,*.onrender.com

# Cloudinary Storage
CLOUDINARY_API_KEY=your-cloudinary-api-key
CLOUDINARY_API_SECRET=your-cloudinary-api-secret
CLOUDINARY_CLOUD_NAME=your-cloudinary-cloud-name

# CORS
CORS_ALLOWED_ORIGINS=https://your-frontend-domain.com,http://localhost:3000
```

### **Other Platforms**
- **Railway**: Use `Procfile` for deployment
- **Heroku**: Use `Procfile` for deployment
- **VPS**: Use `Dockerfile` for containerized deployment

## 🔧 **Technical Stack**

### **Backend**
- **Django 5.1.4**: Web framework
- **Django REST Framework**: API development
- **PostgreSQL**: Production database
- **SQLite**: Development database
- **Gunicorn**: Production WSGI server

### **Storage**
- **Cloudinary**: Production file storage
- **Local Storage**: Development file storage
- **WhiteNoise**: Static file serving

### **Authentication**
- **Django JWT**: Token-based authentication
- **Django Groups**: Permission management

### **Deployment**
- **Docker**: Containerization
- **Render**: Hosting platform
- **Supabase**: PostgreSQL database

## 🛠️ **Development**

### **Admin Panel**
- **URL**: `/eesa/` (not `/admin/`)
- **Features**: 
  - User management with groups
  - Academic resources with verification
  - Content categorization
  - File upload management

### **API Endpoints**
- **Base URL**: `https://your-app.onrender.com/`
- **Authentication**: JWT tokens
- **Documentation**: Check individual app URLs

### **Database Migrations**
```bash
# Create migrations
python manage.py makemigrations

# Apply migrations
python manage.py migrate

# Check migration status
python manage.py showmigrations
```

### **Static Files**
```bash
# Collect static files
python manage.py collectstatic --noinput

# Serve static files (development)
python manage.py runserver
```

## 🔍 **Troubleshooting**

### **Common Issues**

#### **1. Database Connection**
```bash
# Check database settings
python manage.py dbshell

# Verify environment variables
echo $DB_HOST
echo $DB_NAME
```

#### **2. Static Files Not Loading**
```bash
# Collect static files
python manage.py collectstatic --noinput

# Check STATIC_ROOT setting
python manage.py check --deploy
```

#### **3. Migration Issues**
```bash
# Check migration status
python manage.py showmigrations

# Apply migrations
python manage.py migrate
```

#### **4. Docker Issues**
```bash
# Build image
docker build -t eesa-backend .

# Run container
docker run -p 8000:8000 eesa-backend

# Check logs
docker logs <container_id>
```

### **Deployment Issues**

#### **1. Build Failures**
- Check `requirements.txt` for missing dependencies
- Verify Dockerfile configuration
- Check Render logs for specific errors

#### **2. Environment Variables**
- Ensure all required variables are set in Render dashboard
- Check variable names and values
- Verify database connection string

#### **3. ALLOWED_HOSTS**
- Add your domain to ALLOWED_HOSTS
- Use `*` for development, specific domains for production

## 📊 **Monitoring**

### **Health Checks**
```bash
# Check if app is responding
curl -I https://your-app.onrender.com/

# Check admin panel
curl -I https://your-app.onrender.com/eesa/

# Check API root
curl https://your-app.onrender.com/
```

### **Logs**
- **Render**: Dashboard → Your Service → Logs
- **Local**: `python manage.py runserver` output
- **Docker**: `docker logs <container_id>`

## 🔒 **Security**

### **Production Settings**
- ✅ DEBUG=False
- ✅ SECURE_SSL_REDIRECT=True (recommended)
- ✅ SECURE_HSTS_SECONDS=31536000 (recommended)
- ✅ CSRF_COOKIE_SECURE=True (recommended)
- ✅ SESSION_COOKIE_SECURE=True (recommended)

### **Environment Variables**
- ✅ Never commit secrets to git
- ✅ Use environment variables for sensitive data
- ✅ Rotate SECRET_KEY regularly
- ✅ Use strong database passwords

## 🎯 **Best Practices**

### **Code Quality**
- ✅ Follow Django coding style
- ✅ Use meaningful commit messages
- ✅ Test changes locally before deploying
- ✅ Keep dependencies updated

### **Deployment**
- ✅ Use git push for deployment
- ✅ Monitor deployment logs
- ✅ Test after deployment
- ✅ Keep backups of database

### **Development**
- ✅ Use virtual environment
- ✅ Follow git workflow
- ✅ Document changes
- ✅ Review code before merging

## 🎉 **Success!**

**Your backend is now:**
- ✅ **Deployed**: Automatic deployment with git push
- ✅ **Optimized**: Docker multi-stage build
- ✅ **Secure**: Non-root user and proper permissions
- ✅ **Scalable**: PostgreSQL database and Cloudinary storage
- ✅ **Maintainable**: Clean code structure and documentation

**Ready for production!** 🚀

---

**For support**: Check the troubleshooting section or contact the development team.
