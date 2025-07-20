"""
URL configuration for eesa_backend project.
"""
from django.contrib import admin
from django.urls import path, include
from django.conf import settings
from django.conf.urls.static import static
from django.http import JsonResponse
from django.views.decorators.csrf import csrf_exempt

@csrf_exempt
def api_root(request):
    """API root endpoint"""
    return JsonResponse({
        'message': 'EESA Backend API',
        'version': '1.0.0',
        'status': 'operational',
        'admin': '/eesa/'
    })

@csrf_exempt
def health_check(request):
    """Health check endpoint"""
    return JsonResponse({
        'status': 'healthy',
        'message': 'EESA Backend is running'
    })

urlpatterns = [
    path('', api_root, name='api_root'),
    path('api/', api_root, name='api_root_alt'),
    path('health/', health_check, name='health_check'),
    path('eesa/', admin.site.urls),  # Custom admin URL
    
    # API endpoints
    path('api/academics/', include('academics.urls')),
    path('api/projects/', include('projects.urls')),
    path('api/events/', include('events.urls')),
    path('api/placements/', include('placements.urls')),
    path('api/careers/', include('careers.urls')),
    path('api/gallery/', include('gallery.urls')),
    path('api/alumni/', include('alumni.urls')),
]

# Add JWT endpoints if available
try:
    from rest_framework_simplejwt.views import TokenRefreshView
    urlpatterns += [
        path('api/auth/token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),
    ]
except ImportError:
    # JWT not available, skip
    pass

# Serve media files during development
if settings.DEBUG:
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
