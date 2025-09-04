"""
Custom middleware to handle CSRF exemptions for specific API endpoints
"""
from django.utils.deprecation import MiddlewareMixin
from django.views.decorators.csrf import csrf_exempt
from django.conf import settings

class CSRFExemptAPIMiddleware(MiddlewareMixin):
    """
    Middleware to exempt specific API endpoints from CSRF validation
    """
    
    EXEMPT_PATHS = [
        '/api/academics/resources/',  # Covers like and download endpoints
        '/api/accounts/auth/logout/',  # Logout endpoint
    ]
    
    def process_request(self, request):
        """
        Check if the request path should be exempt from CSRF validation
        """
        # Only apply in production
        if settings.DEBUG:
            return None
            
        path = request.path_info
        
        # Check if path matches any exempt patterns
        for exempt_path in self.EXEMPT_PATHS:
            if path.startswith(exempt_path):
                # Mark request as CSRF exempt
                setattr(request, '_dont_enforce_csrf_checks', True)
                break
        
        return None
    
    def process_response(self, request, response):
        """
        Add CORS headers for API endpoints
        """
        if not settings.DEBUG and request.path_info.startswith('/api/'):
            origin = request.META.get('HTTP_ORIGIN')
            if origin:
                # Allow requests from trusted origins
                trusted_origins = getattr(settings, 'CORS_ALLOWED_ORIGINS', [])
                if origin in trusted_origins or any(origin.endswith(domain.replace('https://', '').replace('http://', '')) for domain in trusted_origins):
                    response['Access-Control-Allow-Origin'] = origin
                    response['Access-Control-Allow-Credentials'] = 'true'
                    response['Access-Control-Allow-Methods'] = 'GET, POST, PUT, PATCH, DELETE, OPTIONS'
                    response['Access-Control-Allow-Headers'] = 'Content-Type, X-CSRFToken, X-Requested-With, Authorization'
        
        return response
