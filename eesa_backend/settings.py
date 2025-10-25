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
        'eesacusat.in,www.eesacusat.in,*.eesacusat.in,*.herokuapp.com,*.supabase.co'
    )

# Application definition
INSTALLED_APPS = [
    'jazzmin',  # Must be before django.contrib.admin
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

# Database configuration - Supabase PostgreSQL for production, SQLite for development
if DEBUG:
    print("🗄️ Using SQLite for development")
    DATABASES = {
        'default': {
            'ENGINE': 'django.db.backends.sqlite3',
            'NAME': BASE_DIR / 'db.sqlite3',
        }
    }
else:
    # Production: Use Supabase PostgreSQL with strict limits
    print("🗄️ Using Supabase PostgreSQL")
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
                'connect_timeout': 10,  # Timeout connection attempts quickly
                'options': '-c default_transaction_isolation=read_committed -c statement_timeout=30000'  # 30s query timeout
            },
            'CONN_MAX_AGE': 600,  # Connection pooling (10 min)
            'CONN_HEALTH_CHECKS': True,
            'ATOMIC_REQUESTS': False,
            'AUTOCOMMIT': True,
            # Limit max connections to prevent connection pool exhaustion attacks
            'POOL_OPTIONS': {
                'MAX_OVERFLOW': 5,  # Max overflow connections
                'POOL_SIZE': 5,     # Base pool size (total 10 connections max)
            }
        }
    }
    print("🛡️ Database: Connection pooling enabled, 30s query timeout")

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

# File upload settings - Strict limits to prevent abuse
FILE_UPLOAD_MAX_MEMORY_SIZE = 15 * 1024 * 1024  # 15MB max file size
DATA_UPLOAD_MAX_MEMORY_SIZE = 15 * 1024 * 1024  # 15MB max request size
FILE_UPLOAD_PERMISSIONS = 0o644
DATA_UPLOAD_MAX_NUMBER_FIELDS = 1000  # Limit form fields (prevent memory attacks)

# Additional security: Request size limits (prevent large payload attacks)
if not DEBUG:
    # Production: Strict limits
    FILE_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024  # 10MB in production
    DATA_UPLOAD_MAX_MEMORY_SIZE = 10 * 1024 * 1024
    DATA_UPLOAD_MAX_NUMBER_FIELDS = 500  # Stricter in production
    print("🛡️ File upload limits: 10MB max, 500 max fields")

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

# Security: Rate limiting and throttling to prevent abuse and overbilling attacks
if not DEBUG:
    REST_FRAMEWORK.update({
        'DEFAULT_THROTTLE_CLASSES': [
            'rest_framework.throttling.AnonRateThrottle',
            'rest_framework.throttling.UserRateThrottle',
            'rest_framework.throttling.ScopedRateThrottle',
        ],
        'DEFAULT_THROTTLE_RATES': {
            # Strict limits to prevent DDoS and cost attacks
            'anon': '100/hour',          # Anonymous users: 100 requests/hour
            'user': '1000/hour',         # Authenticated users: 1000 requests/hour
            'burst': '20/minute',        # Burst protection: 20/minute
            'upload': '10/hour',         # File uploads: 10/hour
            'expensive': '10/hour',      # Expensive operations: 10/hour
        },
    })
    print("🛡️ Production rate limiting enabled (100/hr anon, 1000/hr user)")

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

# Caching configuration - Upstash Redis for production, local for development
REDIS_URL = os.environ.get('REDIS_URL') or os.environ.get('UPSTASH_REDIS_URL')

if REDIS_URL:
    # Production/Staging: Use Upstash Redis or any Redis instance
    print(f"🔄 Using Redis cache ({'Upstash' if 'upstash' in REDIS_URL.lower() else 'Redis'})")
    CACHES = {
        'default': {
            'BACKEND': 'django_redis.cache.RedisCache',
            'LOCATION': REDIS_URL,
            'OPTIONS': {
                'CLIENT_CLASS': 'django_redis.client.DefaultClient',
                'CONNECTION_POOL_KWARGS': {
                    'max_connections': 50,
                    'socket_keepalive': True,
                    'retry_on_timeout': True,
                },
                'SOCKET_CONNECT_TIMEOUT': 5,
                'SOCKET_TIMEOUT': 5,
                'COMPRESSOR': 'django_redis.compressors.zlib.ZlibCompressor',
                'SERIALIZER': 'django_redis.serializers.json.JSONSerializer',
                'IGNORE_EXCEPTIONS': True,  # Don't crash if Redis is unavailable
            },
            'KEY_PREFIX': f'eesa_{ENVIRONMENT}',
            'TIMEOUT': 300,  # Default 5 minutes
        }
    }
else:
    # Development: Use local memory cache
    print("🔄 Using local memory cache (no Redis configured)")
    CACHES = {
        'default': {
            'BACKEND': 'django.core.cache.backends.locmem.LocMemCache',
            'LOCATION': 'eesa-dev-cache',
            'OPTIONS': {
                'MAX_ENTRIES': 1000,
            }
        }
    }

# Cache settings
CACHE_TTL = 60 * 60 * 24 if not DEBUG else 60 * 5  # Legacy - use CacheTTL class in utils.redis_cache
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

# Admin site customization - Django admin only (no separate frontend admin)
ADMIN_SITE_HEADER = f"EESA Backend API Administration ({ENVIRONMENT.title()})"
ADMIN_SITE_TITLE = "EESA API Admin"
ADMIN_INDEX_TITLE = f"EESA Backend API Management - {ENVIRONMENT.title()}"

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


# ==========================================
# JAZZMIN ADMIN UI CONFIGURATION
# ==========================================

JAZZMIN_SETTINGS = {
    # Site branding
    "site_title": "EESA Admin",
    "site_header": "⚡ EESA Administration Portal",
    "site_brand": "⚡ EESA Backend",
    "site_logo": None,  # Path to logo in static files
    "login_logo": None,
    "login_logo_dark": None,
    "site_logo_classes": "img-circle",
    "site_icon": None,  # Favicon path
    
    # Welcome text
    "welcome_sign": "Welcome to EESA Admin Panel",
    "copyright": "EESA CUSAT © 2025",
    
    # Search
    "search_model": ["auth.Group", "academics.Subject", "academics.AcademicResource", "events.Event"],
    
    # Top Menu
    "topmenu_links": [
        {"name": "Home", "url": "admin:index", "permissions": ["auth.view_user"]},
        {"name": "API", "url": "/api/", "new_window": True},
    ],
    
    # User menu
    "usermenu_links": [
        {"name": "My Profile", "url": "admin:password_change", "icon": "fas fa-key"},
    ],
    
    # Side Menu - Hide individual models, only show apps
    "show_sidebar": True,
    "navigation_expanded": False,
    "hide_apps": [],
    "hide_models": [
        "academics.Scheme", 
        "academics.Subject", 
        "academics.AcademicResource"
    ],
    
    # Order for apps
    "order_with_respect_to": [
        "auth", 
        "academics", 
        "projects", 
        "events", 
        "gallery", 
        "placements", 
        "careers", 
        "alumni", 
        "accounts"
    ],
    
    # Custom links to add to each app dropdown
    "custom_links": {
        "auth": [{
            "name": "👥 User Groups", 
            "url": "/eesa/auth/group/",
            "icon": "fas fa-users",
            "permissions": ["auth.view_group"]
        }],
        "academics": [{
            "name": "📋 Manage Schemes", 
            "url": "/eesa/academics/scheme/",
            "icon": "fas fa-sitemap",
            "permissions": ["academics.view_scheme"]
        }, {
            "name": "📚 Manage Subjects", 
            "url": "/eesa/academics/subject/",
            "icon": "fas fa-book",
            "permissions": ["academics.view_subject"]
        }, {
            "name": "📄 Manage Resources", 
            "url": "/eesa/academics/academicresource/",
            "icon": "fas fa-file-pdf",
            "permissions": ["academics.view_academicresource"]
        }, {
            "name": "☁️ Bulk Upload PDFs", 
            "url": "/eesa/academics/academicresource/bulk-upload/",
            "icon": "fas fa-cloud-upload-alt",
            "permissions": ["academics.add_academicresource"]
        }]
    },
    
    # Custom icons for apps and models
    "icons": {
        # System
        "auth": "fas fa-shield-alt",
        "auth.Group": "fas fa-users",
        
        # Apps
        "academics": "fas fa-graduation-cap",
        "academics.Scheme": "fas fa-sitemap",
        "academics.Subject": "fas fa-book",
        "academics.AcademicResource": "fas fa-file-pdf",
        
        "events": "fas fa-calendar-check",
        "events.Event": "fas fa-calendar-alt",
        "events.EventRegistration": "fas fa-user-check",
        "events.Notification": "fas fa-bell",
        
        "gallery": "fas fa-images",
        "gallery.Album": "fas fa-folder",
        "gallery.Photo": "fas fa-image",
        
        "projects": "fas fa-project-diagram",
        "projects.Project": "fas fa-code",
        
        "placements": "fas fa-briefcase",
        "placements.Company": "fas fa-building",
        "placements.PlacementDrive": "fas fa-calendar-day",
        "placements.PlacedStudent": "fas fa-user-tie",
        
        "careers": "fas fa-user-tie",
        "careers.JobOpportunity": "fas fa-suitcase",
        "careers.InternshipOpportunity": "fas fa-user-graduate",
        
        "alumni": "fas fa-user-graduate",
        "accounts": "fas fa-user-circle",
    },
    
    # Icons for custom actions
    "default_icon_parents": "fas fa-chevron-circle-right",
    "default_icon_children": "fas fa-circle",
    
    # Related modal
    "related_modal_active": False,
    
    # UI Tweaks
    "custom_css": None,
    "custom_js": None,
    "use_google_fonts_cdn": True,
    "show_ui_builder": False,
    
    # Change view - Better organization
    "changeform_format": "horizontal_tabs",
    "changeform_format_overrides": {
        "auth.Group": "vertical_tabs",
        "academics.AcademicResource": "horizontal_tabs",
        "events.Event": "horizontal_tabs",
        "projects.Project": "horizontal_tabs",
    },
    
    # Language chooser
    "language_chooser": False,
}

JAZZMIN_UI_TWEAKS = {
    "navbar_small_text": False,
    "footer_small_text": False,
    "body_small_text": False,
    "brand_small_text": False,
    "brand_colour": "navbar-primary",
    "accent": "accent-primary",
    "navbar": "navbar-dark",
    "no_navbar_border": False,
    "navbar_fixed": True,
    "layout_boxed": False,
    "footer_fixed": False,
    "sidebar_fixed": True,
    "sidebar": "sidebar-dark-primary",
    "sidebar_nav_small_text": False,
    "sidebar_disable_expand": False,
    "sidebar_nav_child_indent": False,
    "sidebar_nav_compact_style": False,
    "sidebar_nav_legacy_style": False,
    "sidebar_nav_flat_style": False,
    "theme": "default",
    "dark_mode_theme": None,
    "button_classes": {
        "primary": "btn-primary",
        "secondary": "btn-secondary",
        "info": "btn-info",
        "warning": "btn-warning",
        "danger": "btn-danger",
        "success": "btn-success"
    }
}