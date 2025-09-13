"""
EESA Backend Settings - Production Optimized with Development Support
Auto-detects environment and configures accordingly for PostgreSQL/Supabase production
FIXED: HTTP development mode with proper HTTPS redirect control
"""

import os
from pathlib import Path
from django.core.management.utils import get_random_secret_key
from dotenv import load_dotenv

# Build paths inside the project like this: BASE_DIR / 'subdir'.
BASE_DIR = Path(__file__).resolve().parent.parent

# Load environment variables - Production optimized
print("📁 Loading environment variables...")
# Load .env file if it exists (for local development)
load_dotenv(BASE_DIR / '.env')

# Override with environment-specific config
env_type = os.environ.get('DJANGO_ENV', 'development')
if env_type == 'production':
    load_dotenv(BASE_DIR / '.env.production', override=True)
else:
    load_dotenv(BASE_DIR / '.env.development', override=True)

# Environment detection - FIXED: Better debugging
DEBUG_ENV = os.environ.get('DEBUG', 'False')
DEBUG = DEBUG_ENV.lower() in ('true', '1', 'yes', 'on')
ENVIRONMENT = 'development' if DEBUG else 'production'

# Debug environment loading
print(f"🔍 DEBUG from env: '{DEBUG_ENV}'")
print(f"🔍 DEBUG parsed: {DEBUG}")
print(f"🔍 Environment detected: {ENVIRONMENT}")

# Security settings
SECRET_KEY = os.environ.get('SECRET_KEY', get_random_secret_key())

# Helper function for environment variables
def get_list_from_env(key, default_value):
    """Helper to parse comma-separated environment variables"""
    value = os.environ.get(key, default_value)
    if value == '*':
        return ['*']
    return [item.strip() for item in value.split(',') if item.strip()]

# Allowed hosts configuration - production optimized
if DEBUG:
    ALLOWED_HOSTS = ['localhost', '127.0.0.1', '0.0.0.0', '*']
else:
    ALLOWED_HOSTS = get_list_from_env('ALLOWED_HOSTS', 
        'eesacusat.in,www.eesacusat.in,*.eesacusat.in,*.onrender.com,eesabackend.onrender.com,*.railway.app,*.herokuapp.com,*.supabase.co'
    )

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

# Middleware configuration - FIXED: Proper development/production split
if DEBUG:
    print("🔧 Development middleware: Minimal security middleware")
    MIDDLEWARE = [
        'corsheaders.middleware.CorsMiddleware',
        'whitenoise.middleware.WhiteNoiseMiddleware',
        'django.contrib.sessions.middleware.SessionMiddleware',
        'django.middleware.common.CommonMiddleware',
        'django.middleware.csrf.CsrfViewMiddleware',
        'django.contrib.auth.middleware.AuthenticationMiddleware',
        'django.contrib.messages.middleware.MessageMiddleware',
        'django.middleware.clickjacking.XFrameOptionsMiddleware',
    ]
else:
    print("🔒 Production middleware: Full security stack")
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

# Database configuration - PostgreSQL for production, SQLite for development
if DEBUG:
    print("🗄️ Using SQLite for development")
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    # Production: PostgreSQL/Supabase with optimization
    if all([os.environ.get('DB_PASSWORD'), os.environ.get('DB_HOST')]):
        print("🗄️ Using PostgreSQL/Supabase for production")
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.postgresql',
                'NAME': os.environ.get('DB_NAME', 'postgres'),
                'USER': os.environ.get('DB_USER', 'postgres'),
                'PASSWORD': os.environ.get('DB_PASSWORD'),
                'HOST': os.environ.get('DB_HOST'),
                'PORT': os.environ.get('DB_PORT', '5432'),
                'OPTIONS': {
                    'sslmode': 'require',
                    'application_name': 'eesa_backend',
                    'connect_timeout': 10,
                    'options': '-c default_transaction_isolation=read_committed'
                },
                'CONN_MAX_AGE': 600,
                'CONN_HEALTH_CHECKS': True,
                'ATOMIC_REQUESTS': False,
                'AUTOCOMMIT': True,
            }
        }
    else:
        print("⚠️ PostgreSQL not configured, falling back to SQLite")
        DATABASES = {
            'default': {
                'ENGINE': 'django.db.backends.sqlite3',
                'NAME': BASE_DIR / 'db.sqlite3',
            }
        }

# Cloudinary configuration
CLOUDINARY_CONFIG = {
    'cloud_name': os.environ.get('CLOUDINARY_CLOUD_NAME'),
    'api_key': os.environ.get('CLOUDINARY_API_KEY'),
    'api_secret': os.environ.get('CLOUDINARY_API_SECRET'),
    'secure': True,
    'folder': 'eesa_backend'
}

# Storage configuration
if DEBUG:
    print("📁 Using local file storage for development")
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
    if all(CLOUDINARY_CONFIG.values()):
        print("☁️ Using Cloudinary storage for production")
        STORAGES = {
            "default": {
                "BACKEND": "cloudinary_storage.storage.MediaCloudinaryStorage",
            },
            "staticfiles": {
                "BACKEND": "cloudinary_storage.storage.StaticHashedCloudinaryStorage",
            },
        }
        STATICFILES_STORAGE = 'cloudinary_storage.storage.StaticHashedCloudinaryStorage'
    else:
        print("⚠️ Cloudinary not configured, using local storage")
        STORAGES = {
            "default": {
                "BACKEND": "django.core.files.storage.FileSystemStorage",
            },
            "staticfiles": {
                "BACKEND": "django.contrib.staticfiles.storage.StaticFilesStorage",
            },
        }
    
    STATIC_URL = '/static/'
    STATIC_ROOT = BASE_DIR / 'staticfiles'
    MEDIA_URL = '/media/'

# Cloudinary setup for production
if not DEBUG and all(CLOUDINARY_CONFIG.values()):
    import cloudinary
    cloudinary.config(**CLOUDINARY_CONFIG)
    
    CLOUDINARY_STORAGE = {
        'CLOUD_NAME': CLOUDINARY_CONFIG['cloud_name'],
        'API_KEY': CLOUDINARY_CONFIG['api_key'],
        'API_SECRET': CLOUDINARY_CONFIG['api_secret'],
        'MEDIA_TAG': 'eesa_backend_media',
        'STATIC_TAG': 'eesa_backend_static',
    }

# File upload settings
FILE_UPLOAD_MAX_MEMORY_SIZE = 15 * 1024 * 1024  # 15MB
DATA_UPLOAD_MAX_MEMORY_SIZE = 15 * 1024 * 1024  # 15MB
FILE_UPLOAD_PERMISSIONS = 0o644

# Password validation
AUTH_PASSWORD_VALIDATORS = [
    {
        'NAME': 'django.contrib.auth.password_validation.UserAttributeSimilarityValidator',
    },
    {
        'NAME': 'django.contrib.auth.password_validation.MinimumLengthValidator',
        'OPTIONS': {'min_length': 8,}
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
TIME_ZONE = 'Asia/Kolkata' if not DEBUG else 'UTC'
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
    'DEFAULT_RENDERER_CLASSES': [
        'rest_framework.renderers.JSONRenderer',
        'rest_framework.renderers.BrowsableAPIRenderer' if DEBUG else 'rest_framework.renderers.JSONRenderer',
    ] if DEBUG else [
        'rest_framework.renderers.JSONRenderer',
    ],
    'DEFAULT_METADATA_CLASS': 'rest_framework.metadata.SimpleMetadata',
}

# Add throttling for production
if not DEBUG:
    REST_FRAMEWORK.update({
        'DEFAULT_THROTTLE_CLASSES': [
            'rest_framework.throttling.AnonRateThrottle',
            'rest_framework.throttling.UserRateThrottle',
        ],
        'DEFAULT_THROTTLE_RATES': {
            'anon': '100/hour',
            'user': '1000/hour',
        },
    })

# CORS and CSRF configuration - FIXED: Better handling
if DEBUG:
    print("🌐 Development CORS: Allowing local origins with HTTP")
    DEV_ORIGINS = [
        'http://localhost:3000', 'http://127.0.0.1:3000',
        'http://localhost:5173', 'http://127.0.0.1:5173', 
        'http://localhost:8080', 'http://127.0.0.1:8080'
    ]
    CORS_ALLOWED_ORIGINS = get_list_from_env('DEV_CORS_ALLOWED_ORIGINS', ','.join(DEV_ORIGINS))
    CSRF_TRUSTED_ORIGINS = get_list_from_env('DEV_CSRF_TRUSTED_ORIGINS', ','.join(DEV_ORIGINS))
    print(f"🌐 CORS allowed origins: {CORS_ALLOWED_ORIGINS}")
    print(f"🛡️ CSRF trusted origins: {CSRF_TRUSTED_ORIGINS}")
else:
    print("🌐 Production CORS: Secure HTTPS origins only")
    PROD_ORIGINS = ['https://eesacusat.in', 'https://www.eesacusat.in']
    CORS_ALLOWED_ORIGINS = get_list_from_env('CORS_ALLOWED_ORIGINS', ','.join(PROD_ORIGINS))
    CSRF_TRUSTED_ORIGINS = get_list_from_env('CSRF_TRUSTED_ORIGINS', ','.join(PROD_ORIGINS))

CORS_ALLOW_CREDENTIALS = True
CORS_ALLOW_METHODS = ['DELETE', 'GET', 'OPTIONS', 'PATCH', 'POST', 'PUT']
CORS_ALLOW_HEADERS = [
    'accept', 'accept-encoding', 'authorization', 'content-type', 
    'dnt', 'origin', 'user-agent', 'x-csrftoken', 'x-requested-with'
]

# Caching configuration
if not DEBUG and os.environ.get('REDIS_URL'):
    print("🔄 Using Redis cache for production")
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': os.environ.get('REDIS_URL'),
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'CONNECTION_POOL_KWARGS': {
                    'max_connections': 50,
                    'socket_keepalive': True,
                },
                'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
                'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
            },
            'KEY_PREFIX': 'eesa_backend',
            'TIMEOUT': 300,
        }
    }
elif not DEBUG:
    print("🔄 Using database cache for production")
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.db.DatabaseCache',
            'LOCATION': 'eesa_cache_table',
            'TIMEOUT': 300,
            'OPTIONS': {
                'MAX_ENTRIES': 1000,
                'CULL_FREQUENCY': 3,
            }
        }
    }
else:
    print("🔄 Using local memory cache for development")
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'eesa-dev-cache',
        }
    }

# Cache settings
CACHE_TTL = 60 * 60 * 24 if not DEBUG else 60 * 5
CACHE_KEY_PREFIX = f'eesa_{ENVIRONMENT}_'

# Session configuration
SESSION_ENGINE = 'django.contrib.sessions.backends.cache' if not DEBUG else 'django.contrib.sessions.backends.db'
SESSION_CACHE_ALIAS = 'default'
SESSION_COOKIE_AGE = 86400  # 24 hours

# FIXED: Security settings with proper development/production split
if DEBUG:
    print("🔧 Development mode: HTTP allowed, security features disabled")
    # Completely disable HTTPS redirects and security features for development
    SECURE_SSL_REDIRECT = False
    SESSION_COOKIE_SECURE = False
    CSRF_COOKIE_SECURE = False
    SECURE_HSTS_SECONDS = 0
    SECURE_HSTS_INCLUDE_SUBDOMAINS = False
    SECURE_HSTS_PRELOAD = False
    SECURE_BROWSER_XSS_FILTER = False
    SECURE_CONTENT_TYPE_NOSNIFF = False
    X_FRAME_OPTIONS = 'SAMEORIGIN'
    
    # Cookie settings for HTTP development
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    CSRF_COOKIE_HTTPONLY = False  # Allow JS access for development
    CSRF_COOKIE_SAMESITE = 'Lax'
    
    # Remove any proxy headers that might force HTTPS
    # Don't set SECURE_PROXY_SSL_HEADER in development
    
else:
    print("🔒 Production mode: Full HTTPS security enabled")
    # Production: Full security stack
    SECURE_BROWSER_XSS_FILTER = True
    SECURE_CONTENT_TYPE_NOSNIFF = True
    X_FRAME_OPTIONS = 'DENY'
    SECURE_HSTS_SECONDS = 31536000  # 1 year
    SECURE_HSTS_INCLUDE_SUBDOMAINS = True
    SECURE_HSTS_PRELOAD = True
    SECURE_SSL_REDIRECT = True
    SESSION_COOKIE_SECURE = True
    CSRF_COOKIE_SECURE = True
    SECURE_PROXY_SSL_HEADER = ('HTTP_X_FORWARDED_PROTO', 'https')
    SECURE_REFERRER_POLICY = 'strict-origin-when-cross-origin'
    
    # Cookie settings for HTTPS production
    SESSION_COOKIE_HTTPONLY = True
    SESSION_COOKIE_SAMESITE = 'Lax'
    CSRF_COOKIE_HTTPONLY = False
    CSRF_COOKIE_SAMESITE = 'Lax'

# FIXED: Debug output for security settings
print(f"🔒 SECURE_SSL_REDIRECT: {globals().get('SECURE_SSL_REDIRECT', 'NOT SET')}")
print(f"🍪 SESSION_COOKIE_SECURE: {globals().get('SESSION_COOKIE_SECURE', 'NOT SET')}")
print(f"🛡️ CSRF_COOKIE_SECURE: {globals().get('CSRF_COOKIE_SECURE', 'NOT SET')}")
if not DEBUG:
    print(f"🔐 SECURE_PROXY_SSL_HEADER: {globals().get('SECURE_PROXY_SSL_HEADER', 'NOT SET')}")

# Admin site customization - Minimal for production use with separate frontend
ADMIN_SITE_HEADER = f"EESA Backend API Administration ({ENVIRONMENT.title()})"
ADMIN_SITE_TITLE = "EESA API Admin"
ADMIN_INDEX_TITLE = f"EESA Backend API Management - {ENVIRONMENT.title()}"

# Disable admin interface in production if using separate frontend admin
USE_ADMIN_INTERFACE = DEBUG or os.environ.get('ENABLE_ADMIN_INTERFACE', 'False').lower() == 'true'

# Logging configuration
LOGGING = {
    'version': 1,
    'disable_existing_loggers': False,
    'formatters': {
        'verbose': {
            'format': '{levelname} {asctime} {module} {process:d} {thread:d} {message}',
            'style': '{',
        },
        'simple': {
            'format': '{levelname} {message}',
            'style': '{',
        },
    },
    'handlers': {
        'console': {
            'level': 'DEBUG' if DEBUG else 'WARNING',
            'class': 'logging.StreamHandler',
            'formatter': 'simple',
        },
    },
    'loggers': {
        'django': {
            'handlers': ['console'],
            'level': 'INFO',
            'propagate': True,
        },
        'django.db.backends': {
            'handlers': ['console'],
            'level': 'WARNING',
            'propagate': False,
        },
    },
}

# Add file logging for production
if not DEBUG:
    logs_dir = BASE_DIR / 'logs'
    logs_dir.mkdir(exist_ok=True)
    
    LOGGING['handlers']['file'] = {
        'level': 'INFO',
        'class': 'logging.FileHandler',
        'filename': logs_dir / 'django.log',
        'formatter': 'verbose',
    }
    LOGGING['loggers']['django']['handlers'].append('file')

# Email configuration
if not DEBUG:
    EMAIL_BACKEND = 'django.core.mail.backends.smtp.EmailBackend'
    EMAIL_HOST = os.environ.get('EMAIL_HOST', 'smtp.gmail.com')
    EMAIL_PORT = int(os.environ.get('EMAIL_PORT', '587'))
    EMAIL_USE_TLS = True
    EMAIL_HOST_USER = os.environ.get('EMAIL_HOST_USER')
    EMAIL_HOST_PASSWORD = os.environ.get('EMAIL_HOST_PASSWORD')
    DEFAULT_FROM_EMAIL = f"EESA Backend <{EMAIL_HOST_USER}>" if EMAIL_HOST_USER else None
else:
    EMAIL_BACKEND = 'django.core.mail.backends.console.EmailBackend'

# Data export limits
DATA_UPLOAD_MAX_NUMBER_FIELDS = 10000

# Port configuration
PORT = int(os.environ.get('PORT', 8000))

# Performance monitoring for production
if not DEBUG and os.environ.get('SENTRY_DSN'):
    try:
        import logging
        import sentry_sdk
        from sentry_sdk.integrations.django import DjangoIntegration
        from sentry_sdk.integrations.logging import LoggingIntegration
        
        sentry_logging = LoggingIntegration(
            level=logging.INFO,
            event_level=logging.ERROR
        )
        
        sentry_sdk.init(
            dsn=os.environ.get('SENTRY_DSN'),
            integrations=[DjangoIntegration(), sentry_logging],
            traces_sample_rate=0.1,
            send_default_pii=True,
            environment='production'
        )
        print("📊 Sentry monitoring enabled")
    except ImportError:
        print("⚠️ Sentry SDK not installed, skipping monitoring")

# Final status output
print(f"🚀 EESA Backend configured for {ENVIRONMENT.upper()} mode")
if DEBUG:
    print("🔓 HTTP development server ready")
    print(f"📍 Access at: http://127.0.0.1:8000 or http://localhost:8000")
else:
    print("🔒 HTTPS production security enabled")
    if 'postgresql' in DATABASES['default']['ENGINE']:
        print("🗄️ PostgreSQL database connected")
    else:
        print("⚠️ Using SQLite fallback database")
    
    if all(CLOUDINARY_CONFIG.values()):
        print("☁️ Cloudinary storage configured")
    else:
        print("⚠️ Using local storage fallback")