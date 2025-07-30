"""
Django settings for eesa_backend project.
"""

import os
from pathlib import Path
from django.core.management.utils import get_random_secret_key
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables from .env file FIRST
load_dotenv(BASE_DIR / '.env')

# Cloudinary environment variables (define these AFTER loading .env)
CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME')
CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY')
CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET')

# SECURITY WARNING: keep the secret key used in production secret!
SECRET_KEY = os.environ.get('SECRET_KEY', get_random_secret_key())

# SECURITY WARNING: don't run with debug turned on in production!
DEBUG = os.environ.get('DEBUG', 'True').lower() == 'true'

# Handle ALLOWED_HOSTS properly for production
ALLOWED_HOSTS_STR = os.environ.get('ALLOWED_HOSTS', 'localhost,127.0.0.1')
if ALLOWED_HOSTS_STR == '*':
    ALLOWED_HOSTS = ['*']
else:
    ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS_STR.split(',') if host.strip()]

# Add common production hosts and specific domains
if not DEBUG:
    ALLOWED_HOSTS.extend([
        '*.onrender.com',
        'eesabackend.onrender.com',  # Your specific domain
        '*.railway.app',
        '*.herokuapp.com',
        'localhost',
        '127.0.0.1',
        '0.0.0.0'
    ])
    # Remove duplicates while preserving order
    ALLOWED_HOSTS = list(dict.fromkeys(ALLOWED_HOSTS))
    
    # Debug ALLOWED_HOSTS (only if explicitly enabled)
    if DEBUG and os.environ.get('DEBUG_SETTINGS', 'False').lower() == 'true':
        print(f"ALLOWED_HOSTS: {ALLOWED_HOSTS}")
        print(f"DEBUG: {DEBUG}")
        print(f"SECRET_KEY: {'SET' if SECRET_KEY else 'MISSING'}")

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'cloudinary_storage',  # Must come before staticfiles
    'django.contrib.staticfiles',
    'cloudinary',  # Required for cloudinary_storage
    'rest_framework',
    'corsheaders',
    'django_filters',
    'accounts',
    'academics',
    'alumni',
    'careers',
    'events',
    'gallery',
    'placements',
    'projects',
]

MIDDLEWARE = [
    'corsheaders.middleware.CorsMiddleware',
    'django.middleware.security.SecurityMiddleware',
    'whitenoise.middleware.WhiteNoiseMiddleware',  # Add WhiteNoise for static files
    'django.contrib.sessions.middleware.SessionMiddleware',
    'django.middleware.common.CommonMiddleware',
    'django.middleware.csrf.CsrfViewMiddleware',
    'django.contrib.auth.middleware.AuthenticationMiddleware',
    'django.contrib.messages.middleware.MessageMiddleware',
    'django.middleware.clickjacking.XFrameOptionsMiddleware',
]

ROOT_URLCONF = 'eesa_backend.urls'

TEMPLATES = [
    {
        'BACKEND': 'django.template.backends.django.DjangoTemplates',
        'DIRS': [],
        'APP_DIRS': True,
        'OPTIONS': {
            'context_processors': [
                'django.template.context_processors.debug',
                'django.template.context_processors.request',
                'django.contrib.auth.context_processors.auth',
                'django.contrib.messages.context_processors.messages',
            ],
        },
    },
]

WSGI_APPLICATION = 'eesa_backend.wsgi.application'

# Database configuration
if not DEBUG:
    # Production - Use individual DB settings (PostgreSQL)
    db_name = os.environ.get('DB_NAME', 'postgres')
    db_user = os.environ.get('DB_USER', 'postgres')
    db_password = os.environ.get('DB_PASSWORD')
    db_host = os.environ.get('DB_HOST')
    db_port = os.environ.get('DB_PORT', '5432')
    
    # Use PostgreSQL if all variables are set, otherwise SQLite
    if all([db_name, db_user, db_password, db_host]):
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': db_name,
                'USER': db_user,
                'PASSWORD': db_password,
                'HOST': db_host,
                'PORT': db_port,
            }
        }
    else:
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
            }
        }
else:
    # Development - SQLite
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# File storage configuration
# Static files (CSS, JavaScript, Images)
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# File storage configuration - Use local storage in development, Cloudinary in production
if DEBUG:
    # Development: Use local file storage
    DEFAULT_FILE_STORAGE = 'django.core.files.storage.FileSystemStorage'
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'
else:
    # Production: Use Cloudinary for media files
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'

# Static files configuration - Use local storage in development, Cloudinary in production
if DEBUG:
    # Development: Use local static files
    STATICFILES_STORAGE = 'django.contrib.staticfiles.storage.StaticFilesStorage'
    STATIC_URL = '/static/'
    STATIC_ROOT = BASE_DIR / 'staticfiles'
else:
    # Production: Use Cloudinary for static files
    STATICFILES_STORAGE = 'cloudinary_storage.storage.StaticHashedCloudinaryStorage'
    STATIC_URL = f'https://res.cloudinary.com/{CLOUDINARY_CLOUD_NAME}/raw/upload/static/'
    # STATIC_ROOT is still needed for collectstatic command
    STATIC_ROOT = BASE_DIR / 'staticfiles'

# Cloudinary configuration - Only used in production
if not DEBUG:
    import cloudinary
    import cloudinary.uploader
    import cloudinary.api

    cloudinary.config(
        cloud_name=CLOUDINARY_CLOUD_NAME,
        api_key=CLOUDINARY_API_KEY,
        api_secret=CLOUDINARY_API_SECRET,
        secure=True
    )

# Media URL configuration - Use local in development, Cloudinary in production
if not DEBUG:
    MEDIA_URL = f'https://res.cloudinary.com/{CLOUDINARY_CLOUD_NAME}/raw/upload/'

# Cloudinary storage configuration - Only used in production
if not DEBUG:
    CLOUDINARY_STORAGE = {
        'CLOUD_NAME': CLOUDINARY_CLOUD_NAME,
        'API_KEY': CLOUDINARY_API_KEY,
        'API_SECRET': CLOUDINARY_API_SECRET,
        'STATICFILES_MANIFEST_ROOT': '',
        'STATICFILES_MANIFEST_STRICT': False,
        'STATICFILES_USE_MANIFEST': False,
        'RESOURCE_TYPE': 'raw',  # Use 'raw' for PDF files to ensure they're not treated as images
        'SECURE': True,
        'INVALID_VIDEO_ERROR': False,
        'STATIC_TRANSFORMATIONS': {
            'pdf': {'resource_type': 'raw', 'format': 'pdf'},
        },
        # Additional settings for better PDF handling
        'MAGIC_FILE_PATH': None,  # Disable magic file detection for better performance
        'ALLOWED_EXTENSIONS': ['pdf'],  # Explicitly allow PDF files
        # Static files settings
        'STATICFILES_DIRS': [],
        'STATICFILES_STORAGE': 'cloudinary_storage.storage.StaticHashedCloudinaryStorage',
    }

# STATIC_ROOT is already defined in the DEBUG conditional above

# Cloudinary settings - Use Cloudinary for both development and production
CLOUDINARY_URL = os.environ.get('CLOUDINARY_URL')

# Cloudinary configuration validation
if DEBUG and not all([CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET]):
    print("Warning: Cloudinary configuration incomplete - will use local storage in development")
    print("Please set all required Cloudinary environment variables for production:")
    print("- CLOUDINARY_CLOUD_NAME") 
    print("- CLOUDINARY_API_KEY")
    print("- CLOUDINARY_API_SECRET")

# Validate Cloudinary configuration for production
if not DEBUG and not all([CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET]):
    raise ValueError("Cloudinary configuration required for production. Please set all required environment variables.")

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.CommonPasswordValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.NumericPasswordValidator',
    },
]

# Internationalization
LANGUAGE_CODE = 'en-us'
TIME_ZONE = 'UTC'
USE_I18N = True
USE_TZ = True

# Default primary key field type
DEFAULT_AUTO_FIELD = 'django.db.models.BigAutoField'

# Custom User Model
AUTH_USER_MODEL = 'accounts.User'

# REST Framework
REST_FRAMEWORK = {
    'DEFAULT_AUTHENTICATION_CLASSES': [
        'rest_framework.authentication.SessionAuthentication',
        'rest_framework.authentication.TokenAuthentication',
    ],
    'DEFAULT_PERMISSION_CLASSES': [
        'rest_framework.permissions.IsAuthenticatedOrReadOnly',
    ],
    'DEFAULT_FILTER_BACKENDS': [
        'django_filters.rest_framework.DjangoFilterBackend',
        'rest_framework.filters.SearchFilter',
        'rest_framework.filters.OrderingFilter',
    ],
    'DEFAULT_PAGINATION_CLASS': 'rest_framework.pagination.PageNumberPagination',
    'PAGE_SIZE': 20,
}

# CORS settings
import os

# CORS Origins based on environment
if DEBUG:
    # Development CORS settings from environment or empty list
    dev_cors = os.environ.get('DEV_CORS_ALLOWED_ORIGINS', 'http://localhost:3000,http://127.0.0.1:3000,http://localhost:5173,http://127.0.0.1:5173')
    CORS_ALLOWED_ORIGINS = [origin.strip() for origin in dev_cors.split(',') if origin.strip()]
else:
    # Production CORS settings - must be set in environment
    cors_origins = os.environ.get('CORS_ALLOWED_ORIGINS', '')
    CORS_ALLOWED_ORIGINS = [origin.strip() for origin in cors_origins.split(',') if origin.strip()]
    
    # Debug CORS settings (only if explicitly enabled)
    if DEBUG and os.environ.get('DEBUG_SETTINGS', 'False').lower() == 'true':
        print(f"CORS_ALLOWED_ORIGINS: {CORS_ALLOWED_ORIGINS}")

# Additional CORS settings
CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = [
    'DELETE',
    'GET',
    'OPTIONS',
    'PATCH',
    'POST',
    'PUT',
]

CORS_ALLOW_HEADERS = [
    'accept',
    'accept-encoding',
    'authorization',
    'content-type',
    'dnt',
    'origin',
    'user-agent',
    'x-csrftoken',
    'x-requested-with',
]

# Admin site customization
ADMIN_SITE_HEADER = "EESA Backend Administration"
ADMIN_SITE_TITLE = "EESA Admin Portal"
ADMIN_INDEX_TITLE = "Welcome to EESA Backend Administration"

# Cache Configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'eesa-cache',
    }
}

# Cache time to live is 365 days
CACHE_TTL = 60 * 60 * 24 * 365

# Key prefix for cache to avoid conflicts
CACHE_KEY_PREFIX = 'eesa_'

# Storage configuration validation (only in development)
if DEBUG and not all([CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET]):
    print("Warning: Cloudinary storage not properly configured")