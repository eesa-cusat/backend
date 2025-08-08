"""
Django settings for eesa_backend project.
Production-optimized configuration.
"""

import os
from pathlib import Path
from django.core.management.utils import get_random_secret_key
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables
load_dotenv(BASE_DIR / '.env', override=False)

# Cloudinary configuration
CLOUDINARY_CLOUD_NAME = os.environ.get('CLOUDINARY_CLOUD_NAME')
CLOUDINARY_API_KEY = os.environ.get('CLOUDINARY_API_KEY')
CLOUDINARY_API_SECRET = os.environ.get('CLOUDINARY_API_SECRET')

# Security settings
SECRET_KEY = os.environ.get('SECRET_KEY', get_random_secret_key())
DEBUG = os.environ.get('DEBUG', 'False').lower() == 'true'

# Allowed hosts configuration
# Default to localhost in DEBUG, and to only the API and WWW domains in production
ALLOWED_HOSTS_STR = os.environ.get(
    'ALLOWED_HOSTS',
    'localhost,127.0.0.1' if DEBUG else 'api.eesacusat.in,www.eesacusat.in'
)
if ALLOWED_HOSTS_STR == '*':
    ALLOWED_HOSTS = ['*']
else:
    ALLOWED_HOSTS = [host.strip() for host in ALLOWED_HOSTS_STR.split(',') if host.strip()]

# In production, keep ALLOWED_HOSTS tight to avoid unintended exposure.
# Use the environment variable to expand if needed.

# Application definition
INSTALLED_APPS = [
    'django.contrib.admin',
    'django.contrib.auth',
    'django.contrib.contenttypes',
    'django.contrib.sessions',
    'django.contrib.messages',
    'cloudinary_storage',
    'django.contrib.staticfiles',
    'cloudinary',
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
    'whitenoise.middleware.WhiteNoiseMiddleware',
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
if DEBUG:
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    # Production - PostgreSQL with fallback to SQLite
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.postgresql',
            'NAME': os.environ.get('DB_NAME', 'postgres'),
            'USER': os.environ.get('DB_USER', 'postgres'),
            'PASSWORD': os.environ.get('DB_PASSWORD'),
            'HOST': os.environ.get('DB_HOST'),
            'PORT': os.environ.get('DB_PORT', '5432'),
        }
    } if all([os.environ.get('DB_PASSWORD'), os.environ.get('DB_HOST')]) else {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }

# File storage configuration
STATICFILES_FINDERS = [
    'django.contrib.staticfiles.finders.FileSystemFinder',
    'django.contrib.staticfiles.finders.AppDirectoriesFinder',
]

# Storage configuration based on environment
if DEBUG:
    # Development: Local storage
    STORAGES = {
        "default": {
            "BACKEND": "django.core.files.storage.FileSystemStorage",
        },
        "staticfiles": {
            "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
        },
    }
    MEDIA_URL = '/media/'
    MEDIA_ROOT = BASE_DIR / 'media'
    STATIC_URL = '/static/'
    STATIC_ROOT = BASE_DIR / 'staticfiles'
else:
    # Production: Cloudinary storage
    STORAGES = {
        "default": {
            "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
        },
        "staticfiles": {
            "BACKEND": "cloudinary_storage.storage.StaticHashedCloudinaryStorage",
        },
    }
    # Backward compatibility for cloudinary_storage package
    DEFAULT_FILE_STORAGE = 'cloudinary_storage.storage.MediaCloudinaryStorage'
    STATICFILES_STORAGE = 'cloudinary_storage.storage.StaticHashedCloudinaryStorage'
    
    STATIC_URL = '/static/'
    STATIC_ROOT = BASE_DIR / 'staticfiles'
    MEDIA_URL = '/media/'

# Cloudinary configuration for production
if not DEBUG and all([CLOUDINARY_CLOUD_NAME, CLOUDINARY_API_KEY, CLOUDINARY_API_SECRET]):
    import cloudinary
    cloudinary.config(
        cloud_name=CLOUDINARY_CLOUD_NAME,
        api_key=CLOUDINARY_API_KEY,
        api_secret=CLOUDINARY_API_SECRET,
        secure=True
    )

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

# REST Framework configuration
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

# CORS configuration
if DEBUG:
    # Development CORS settings
    dev_cors = os.environ.get(
        'DEV_CORS_ALLOWED_ORIGINS',
        'http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001,http://localhost:5173,http://127.0.0.1:5173'
    )
    CORS_ALLOWED_ORIGINS = [origin.strip() for origin in dev_cors.split(',') if origin.strip()]
else:
    # Behind a proxy in production, CORS is not needed for same-origin requests
    CORS_ALLOWED_ORIGINS = []

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

# CSRF configuration
CSRF_COOKIE_HTTPONLY = False  # Allow JavaScript to read CSRF token
CSRF_COOKIE_SAMESITE = 'Lax'
CSRF_COOKIE_SECURE = False if DEBUG else True  # Only secure in production
CSRF_USE_SESSIONS = False

# Session configuration
SESSION_COOKIE_SAMESITE = 'Lax'
SESSION_COOKIE_SECURE = False if DEBUG else True  # Only secure in production
SESSION_COOKIE_HTTPONLY = True
SESSION_COOKIE_AGE = 86400  # 24 hours

# Cookie domains for production (use parent domain; never the subdomain)
if not DEBUG:
    SESSION_COOKIE_DOMAIN = '.eesacusat.in'
    CSRF_COOKIE_DOMAIN = '.eesacusat.in'
if DEBUG:
    # Development CSRF settings - allow frontend origins
    dev_csrf = os.environ.get('DEV_CSRF_TRUSTED_ORIGINS', 
                             'http://localhost:3000,http://127.0.0.1:3000,http://localhost:3001,http://127.0.0.1:3001,http://localhost:5173,http://127.0.0.1:5173')
    CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in dev_csrf.split(',') if origin.strip()]
else:
    # Production CSRF settings: only trust the main site by default. Add api subdomain via env if needed.
    csrf_origins = os.environ.get('CSRF_TRUSTED_ORIGINS', 'https://www.eesacusat.in')
    CSRF_TRUSTED_ORIGINS = [origin.strip() for origin in csrf_origins.split(',') if origin.strip()]

# Admin site customization
ADMIN_SITE_HEADER = "EESA Backend Administration"
ADMIN_SITE_TITLE = "EESA Admin Portal"
ADMIN_INDEX_TITLE = "Welcome to EESA Backend Administration"

# Cache configuration
CACHES = {
    'default': {
        'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
        'LOCATION': 'eesa-cache',
    }
}

# Cache settings
CACHE_TTL = 60 * 60 * 24 * 365  # 1 year
CACHE_KEY_PREFIX = 'eesa_'

# Production security settings (behind proxy/CDN)
if not DEBUG:
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    # Critical to avoid HTTPS redirect loops behind a proxy
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')

# Port configuration for deployment platforms
import os
PORT = int(os.environ.get('PORT', 8000))