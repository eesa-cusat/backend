"""
URL configuration for eesa_backend project.
Production-optimized URL configuration.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt
from django.views.decorators.cache import cache_page
from django.views.decorators.http import require_http_methods

@csrf_exempt
@require_http_methods(["GET"])
@cache_page(60 * 15)  # Cache for 15 minutes
def api_root(request):
    """API root endpoint with basic API information"""
    return JsonResponse({
        'message': 'EESA Backend API',
        'version': '1.0.0',
        'status': 'operational',
        'admin': '/eesa/',
        'endpoints': {
            'academics': '/api/academics/',
            'projects': '/api/projects/',
            'events': '/api/events/',
            'placements': '/api/placements/',
            'careers': '/api/careers/',
            'gallery': '/api/gallery/',
            'alumni': '/api/alumni/',
            'accounts': '/api/accounts/',
            'team': '/api/team/'
        }
    })

@csrf_exempt
@require_http_methods(["GET"])
def health_check(request):
    """Health check endpoint for monitoring"""
    return JsonResponse({
        'status': 'healthy',
        'message': 'EESA Backend is running',
        'debug': settings.DEBUG
    })

@csrf_exempt
@require_http_methods(["GET"])
@cache_page(60 * 30)  # Cache for 30 minutes
def team_members(request):
    """Team members endpoint"""
    return JsonResponse({
        'team': [
            {
                'name': 'Development Team',
                'role': 'Backend Development',
                'description': 'EESA College Portal Backend Team'
            }
        ],
        'message': 'Team members data - Connect to actual team model if needed'
    })

# Core URL patterns
urlpatterns = [
    # Root and health endpoints
    path('', api_root, name='api_root'),
    path('api/', api_root, name='api_root_alt'),
    path('health/', health_check, name='health_check'),
    
    # Admin panel with custom URL
    path('eesa/', admin.site.urls),
    
    # API endpoints - organized by feature
    path('api/academics/', include('academics.urls')),
    path('api/projects/', include('projects.urls')),
    path('api/events/', include('events.urls')),
    path('api/placements/', include('placements.urls')),
    path('api/careers/', include('careers.urls')),
    path('api/gallery/', include('gallery.urls')),
    path('api/alumni/', include('alumni.urls')),
    path('api/accounts/', include('accounts.urls')),
    path('api/team/', team_members, name='team_members'),
]

# Add JWT authentication endpoints if available
try:
    from rest_framework_simplejwt.views import TokenRefreshView
    urlpatterns += [
        path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    ]
except ImportError:
    pass

# Development-only: Serve static and media files
if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
