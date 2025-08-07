# Production Deployment Guide

## Pre-deployment Checklist

### Environment Setup
1. **Environment Variables**: Copy `.env.example` to `.env` and configure:
   - `DEBUG=False` (CRITICAL for production)
   - Set secure `SECRET_KEY`
   - Configure database settings (PostgreSQL recommended)
   - Set up Cloudinary for file storage
   - Configure allowed hosts and CORS settings

2. **Database**: 
   - Use PostgreSQL for production (not SQLite)
   - Run migrations: `python manage.py migrate`
   - Create superuser: `python manage.py createsuperuser`
   - Create user groups (academics_team, careers_team, etc.)

3. **Static Files**: 
   - Run `python manage.py collectstatic`
   - Configure static file serving (nginx/cloudinary)

### Security Configuration
- Ensure `DEBUG=False` in production
- Set secure `SECRET_KEY`
- Configure `ALLOWED_HOSTS` with your domain(s)
- Set up proper CORS settings
- Configure SSL/HTTPS

### File Storage
- Configure Cloudinary for media file storage
- Set up proper file upload permissions
- Ensure backup strategy for uploaded files

## Deployment Steps

1. **Clone Repository**
   ```bash
   git clone <repository-url>
   cd backend
   ```

2. **Install Dependencies**
   ```bash
   pip install -r requirements.txt
   ```

3. **Configure Environment**
   ```bash
   cp .env.example .env
   # Edit .env with production values
   ```

4. **Database Setup**
   ```bash
   # Generate fresh migrations in correct order (since we removed old ones for clean deployment)
   # Create migrations for core apps first
   python manage.py makemigrations accounts
   
   # Then create migrations for all apps
   python manage.py makemigrations
   
   # Run all migrations
   python manage.py migrate
   
   # Create superuser
   python manage.py createsuperuser
   ```

5. **Create User Groups**
   ```bash
   python manage.py shell
   >>> from django.contrib.auth.models import Group
   >>> Group.objects.create(name='academics_team')
   >>> Group.objects.create(name='careers_team')
   >>> Group.objects.create(name='events_team')
   >>> Group.objects.create(name='people_team')
   ```

6. **Collect Static Files**
   ```bash
   python manage.py collectstatic --noinput
   ```

7. **Test Configuration**
   ```bash
   python manage.py check --deploy
   ```

## Post-deployment

### Admin Panel Setup
1. Access `/admin/` with superuser credentials
2. Add users to appropriate groups
3. Configure basic data (schemes, subjects if needed)

### Monitoring
- Set up logging
- Monitor file uploads
- Check API endpoints
- Verify permissions are working correctly

## Backup Strategy
- Regular database backups
- Backup uploaded media files
- Environment configuration backup

## Security Notes
- Never commit `.env` files
- Use strong passwords
- Enable rate limiting if needed
- Monitor for suspicious activity
- Keep dependencies updated
