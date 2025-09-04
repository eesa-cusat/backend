"""
Rate limiting utilities for API endpoints
"""
from functools import wraps
from django.core.cache import cache
from django.http import JsonResponse
from rest_framework.response import Response
from rest_framework import status
import time

def rate_limit(max_requests=10, window_seconds=60, key_func=None):
    """
    Rate limiting decorator for API views
    
    Args:
        max_requests: Maximum number of requests allowed
        window_seconds: Time window in seconds
        key_func: Function to generate cache key (default uses IP)
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Generate cache key
            if key_func:
                cache_key = key_func(request)
            else:
                # Default: use IP address
                from academics.views import get_client_ip
                ip = get_client_ip(request)
                cache_key = f"rate_limit:{view_func.__name__}:{ip}"
            
            # Get current request count
            current_requests = cache.get(cache_key, 0)
            
            if current_requests >= max_requests:
                return Response({
                    'error': 'Rate limit exceeded',
                    'message': f'Too many requests. Maximum {max_requests} requests per {window_seconds} seconds.',
                    'retry_after': window_seconds
                }, status=status.HTTP_429_TOO_MANY_REQUESTS)
            
            # Increment request count
            cache.set(cache_key, current_requests + 1, window_seconds)
            
            # Call the original view
            return view_func(request, *args, **kwargs)
        
        return wrapper
    return decorator

def rate_limit_by_ip_and_resource(max_requests=5, window_seconds=60):
    """
    Rate limiting by IP and resource combination
    Useful for like/download endpoints
    """
    def key_func(request):
        from academics.views import get_client_ip
        ip = get_client_ip(request)
        resource_id = request.resolver_match.kwargs.get('pk', 'unknown')
        return f"rate_limit_resource:{request.resolver_match.url_name}:{ip}:{resource_id}"
    
    return rate_limit(max_requests=max_requests, window_seconds=window_seconds, key_func=key_func)
