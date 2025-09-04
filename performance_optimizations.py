# Advanced Performance Optimizations for EESA Backend
# This file contains additional optimization utilities

import time
from functools import wraps
from django.core.cache import cache
from django.http import JsonResponse
from django.conf import settings

class PerformanceMiddleware:
    """Middleware to add performance metrics to responses"""
    
    def __init__(self, get_response):
        self.get_response = get_response

    def __call__(self, request):
        start_time = time.time()
        
        response = self.get_response(request)
        
        # Add performance headers
        process_time = time.time() - start_time
        response['X-Process-Time'] = str(process_time)
        
        # Add cache hit/miss info for API endpoints
        if hasattr(request, 'cache_hit'):
            response['X-Cache-Status'] = 'HIT' if request.cache_hit else 'MISS'
            
        return response

def cache_response(timeout=300, key_prefix=''):
    """Decorator for caching API responses"""
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Generate cache key from request
            cache_key = f"{key_prefix}_{request.path}_{request.GET.urlencode()}"
            
            # Try to get from cache
            cached_response = cache.get(cache_key)
            if cached_response:
                request.cache_hit = True
                return JsonResponse(cached_response)
            
            # Get fresh response
            response = view_func(request, *args, **kwargs)
            request.cache_hit = False
            
            # Cache the response data
            if hasattr(response, 'data'):
                cache.set(cache_key, response.data, timeout)
            
            return response
        return wrapper
    return decorator

def smart_pagination(queryset, request, serializer_class, page_size=20):
    """Optimized pagination with prefetch"""
    from django.core.paginator import Paginator
    from rest_framework.response import Response
    
    # Get page number
    page = int(request.GET.get('page', 1))
    
    # Create paginator
    paginator = Paginator(queryset, page_size)
    page_obj = paginator.get_page(page)
    
    # Serialize data
    serializer = serializer_class(page_obj.object_list, many=True)
    
    return Response({
        'results': serializer.data,
        'count': paginator.count,
        'page': page,
        'pages': paginator.num_pages,
        'has_next': page_obj.has_next(),
        'has_previous': page_obj.has_previous(),
    })
