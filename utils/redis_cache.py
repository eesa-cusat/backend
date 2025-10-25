"""
Redis Caching Utility for EESA Backend
Provides centralized caching functions for all modules with Upstash Redis support
"""

import json
import logging
from functools import wraps
from typing import Any, Callable, Optional, Union
from django.core.cache import cache
from django.conf import settings

logger = logging.getLogger(__name__)


# ============================================
# Cache TTL Constants (in seconds)
# ============================================
class CacheTTL:
    """Cache Time-To-Live configurations based on data freshness requirements"""
    
    # Static content - rarely changes
    PERMANENT = 60 * 60 * 24 * 7  # 1 week
    ABOUT_US = 60 * 60 * 24 * 7   # 1 week
    PROGRAMS = 60 * 60 * 24 * 7   # 1 week
    BATCHES = 60 * 60 * 24 * 7    # 1 week
    
    # Semi-static content - changes occasionally
    GALLERY_ALBUMS = 60 * 60 * 24 * 7  # 1 week
    
    # Dynamic content - moderate freshness
    EVENTS_LIST = 60 * 30           # 30 minutes
    EVENTS_DETAIL = 60 * 10         # 10 minutes
    PROJECTS_LIST = 60 * 15         # 15 minutes
    CAREERS_JOBS = 60 * 30          # 30 minutes
    ALUMNI_BATCH_STUDENTS = 60 * 10 # 10 minutes
    
    # Highly dynamic content - frequent updates
    GALLERY_ALBUM_DETAIL = 60 * 10  # 10 minutes
    NOTES_LIST = 60 * 5             # 5 minutes
    NOTES_SUBJECT = 60 * 1          # 1 minute
    
    # Default fallback
    DEFAULT = 60 * 5                # 5 minutes


# ============================================
# Cache Key Generators
# ============================================
def generate_cache_key(prefix: str, *args, **kwargs) -> str:
    """
    Generate a structured cache key with consistent format
    
    Args:
        prefix: Cache key prefix (module:object_type)
        *args: Additional positional identifiers
        **kwargs: Additional key-value pairs for the key
    
    Returns:
        Formatted cache key string
    
    Examples:
        generate_cache_key('gallery:albums', type='eesa')
        -> 'gallery:albums:type:eesa'
        
        generate_cache_key('events:detail', 123)
        -> 'events:detail:123'
        
        generate_cache_key('alumni:batch', 2020, 'students', page=1)
        -> 'alumni:batch:2020:students:page:1'
    """
    key_parts = [prefix]
    
    # Add positional arguments
    for arg in args:
        key_parts.append(str(arg))
    
    # Add keyword arguments
    for k, v in sorted(kwargs.items()):
        if v is not None:
            key_parts.extend([str(k), str(v)])
    
    return ':'.join(key_parts)


def generate_list_cache_key(prefix: str, page: Optional[int] = None, **filters) -> str:
    """
    Generate cache key for paginated lists with filters
    
    Args:
        prefix: Cache key prefix
        page: Page number for pagination
        **filters: Filter parameters
    
    Returns:
        Cache key for the list
    """
    key_parts = {'page': page} if page else {}
    key_parts.update(filters)
    return generate_cache_key(f"{prefix}:list", **key_parts)


# ============================================
# Core Caching Functions
# ============================================
def get_cached_data(cache_key: str) -> Optional[Any]:
    """
    Retrieve data from Redis cache
    
    Args:
        cache_key: The cache key to retrieve
    
    Returns:
        Cached data if found, None otherwise
    """
    try:
        cached_data = cache.get(cache_key)
        if cached_data is not None:
            logger.debug(f"Cache HIT: {cache_key}")
            return cached_data
        logger.debug(f"Cache MISS: {cache_key}")
        return None
    except Exception as e:
        logger.error(f"Cache GET error for key '{cache_key}': {str(e)}")
        return None


def set_cached_data(cache_key: str, data: Any, ttl: int = CacheTTL.DEFAULT) -> bool:
    """
    Store data in Redis cache
    
    Args:
        cache_key: The cache key
        data: Data to cache (will be JSON serialized)
        ttl: Time-to-live in seconds
    
    Returns:
        True if successful, False otherwise
    """
    try:
        cache.set(cache_key, data, timeout=ttl)
        logger.debug(f"Cache SET: {cache_key} (TTL: {ttl}s)")
        return True
    except Exception as e:
        logger.error(f"Cache SET error for key '{cache_key}': {str(e)}")
        return False


def invalidate_cache(cache_key: str) -> bool:
    """
    Delete a specific cache entry
    
    Args:
        cache_key: The cache key to delete
    
    Returns:
        True if successful, False otherwise
    """
    try:
        cache.delete(cache_key)
        logger.info(f"Cache INVALIDATED: {cache_key}")
        return True
    except Exception as e:
        logger.error(f"Cache DELETE error for key '{cache_key}': {str(e)}")
        return False


def invalidate_cache_pattern(pattern: str) -> int:
    """
    Delete all cache entries matching a pattern
    
    Args:
        pattern: Pattern to match (e.g., 'events:*', 'projects:list:*')
    
    Returns:
        Number of keys deleted
    """
    try:
        # django-redis supports delete_pattern
        deleted_count = cache.delete_pattern(pattern)
        logger.info(f"Cache PATTERN INVALIDATED: {pattern} ({deleted_count} keys)")
        return deleted_count
    except AttributeError:
        # Fallback for cache backends that don't support pattern deletion
        logger.warning(f"Cache backend doesn't support pattern deletion: {pattern}")
        return 0
    except Exception as e:
        logger.error(f"Cache PATTERN DELETE error for pattern '{pattern}': {str(e)}")
        return 0


def get_or_set_cache(cache_key: str, fetch_func: Callable, ttl: int = CacheTTL.DEFAULT) -> Any:
    """
    Get data from cache or fetch and cache it if not found
    
    Args:
        cache_key: The cache key
        fetch_func: Function to call if cache miss (should return data)
        ttl: Time-to-live in seconds
    
    Returns:
        Cached or freshly fetched data
    """
    # Try to get from cache first
    cached_data = get_cached_data(cache_key)
    if cached_data is not None:
        return cached_data
    
    # Cache miss - fetch fresh data
    try:
        fresh_data = fetch_func()
        set_cached_data(cache_key, fresh_data, ttl)
        return fresh_data
    except Exception as e:
        logger.error(f"Error fetching data for cache key '{cache_key}': {str(e)}")
        raise


# ============================================
# Decorator for View Caching
# ============================================
def cache_response(cache_key_func: Callable, ttl: int = CacheTTL.DEFAULT):
    """
    Decorator to cache view responses
    
    Args:
        cache_key_func: Function that generates cache key from request
        ttl: Time-to-live in seconds
    
    Usage:
        @cache_response(lambda req: f'events:list:page:{req.GET.get("page", 1)}', CacheTTL.EVENTS_LIST)
        def events_list(request):
            ...
    """
    def decorator(view_func):
        @wraps(view_func)
        def wrapper(request, *args, **kwargs):
            # Generate cache key
            cache_key = cache_key_func(request, *args, **kwargs)
            
            # Try to get from cache
            cached_response = get_cached_data(cache_key)
            if cached_response is not None:
                return cached_response
            
            # Cache miss - execute view
            response = view_func(request, *args, **kwargs)
            
            # Cache the response
            set_cached_data(cache_key, response, ttl)
            
            return response
        return wrapper
    return decorator


# ============================================
# Module-Specific Cache Helpers
# ============================================

class GalleryCache:
    """Cache helpers for Gallery module"""
    
    @staticmethod
    def albums_list_key(album_type: Optional[str] = None, page: Optional[int] = None) -> str:
        """Generate cache key for gallery albums list"""
        return generate_cache_key('gallery:albums', type=album_type or 'all', page=page or 1)
    
    @staticmethod
    def album_detail_key(album_id: int) -> str:
        """Generate cache key for album detail"""
        return generate_cache_key('gallery:album', album_id)
    
    @staticmethod
    def invalidate_albums(album_type: Optional[str] = None):
        """Invalidate gallery albums cache"""
        if album_type:
            invalidate_cache_pattern(f'gallery:albums:type:{album_type}:*')
        else:
            invalidate_cache_pattern('gallery:albums:*')
    
    @staticmethod
    def invalidate_album(album_id: int):
        """Invalidate specific album cache"""
        invalidate_cache(GalleryCache.album_detail_key(album_id))


class EventsCache:
    """Cache helpers for Events module"""
    
    @staticmethod
    def events_list_key(page: int = 1, event_type: Optional[str] = None, **filters) -> str:
        """Generate cache key for events list"""
        return generate_cache_key('events:list', page=page, event_type=event_type, **filters)
    
    @staticmethod
    def event_detail_key(event_id: int) -> str:
        """Generate cache key for event detail"""
        return generate_cache_key('events:detail', event_id)
    
    @staticmethod
    def invalidate_events_list():
        """Invalidate all events list caches"""
        invalidate_cache_pattern('events:list:*')
    
    @staticmethod
    def invalidate_event(event_id: int):
        """Invalidate specific event cache"""
        invalidate_cache(EventsCache.event_detail_key(event_id))
        invalidate_cache_pattern('events:list:*')  # Also invalidate list


class ProjectsCache:
    """Cache helpers for Projects module"""
    
    @staticmethod
    def projects_list_key(page: int = 1, category: Optional[str] = None, year: Optional[str] = None) -> str:
        """Generate cache key for projects list"""
        return generate_cache_key('projects:list', page=page, category=category, year=year)
    
    @staticmethod
    def project_detail_key(project_id: int) -> str:
        """Generate cache key for project detail"""
        return generate_cache_key('projects:detail', project_id)
    
    @staticmethod
    def invalidate_projects_list():
        """Invalidate all projects list caches"""
        invalidate_cache_pattern('projects:list:*')
    
    @staticmethod
    def invalidate_project(project_id: int):
        """Invalidate specific project cache"""
        invalidate_cache(ProjectsCache.project_detail_key(project_id))
        invalidate_cache_pattern('projects:list:*')


class AlumniCache:
    """Cache helpers for Alumni module"""
    
    @staticmethod
    def batches_list_key() -> str:
        """Generate cache key for batches list"""
        return generate_cache_key('alumni:batches')
    
    @staticmethod
    def batch_students_key(batch_year: str, page: int = 1) -> str:
        """Generate cache key for batch students"""
        return generate_cache_key('alumni:batch', batch_year, 'students', page=page)
    
    @staticmethod
    def invalidate_batches():
        """Invalidate batches list cache"""
        invalidate_cache(AlumniCache.batches_list_key())
    
    @staticmethod
    def invalidate_batch_students(batch_year: str):
        """Invalidate batch students cache for all pages"""
        invalidate_cache_pattern(f'alumni:batch:{batch_year}:students:*')


class AcademicsCache:
    """Cache helpers for Academics module"""
    
    @staticmethod
    def programs_key() -> str:
        """Generate cache key for academic programs"""
        return generate_cache_key('academics:programs')
    
    @staticmethod
    def notes_subject_key(subject_id: int, year: Optional[int] = None) -> str:
        """Generate cache key for notes by subject"""
        return generate_cache_key('notes:subject', subject_id, year=year)
    
    @staticmethod
    def invalidate_programs():
        """Invalidate academic programs cache"""
        invalidate_cache(AcademicsCache.programs_key())
    
    @staticmethod
    def invalidate_notes_subject(subject_id: int):
        """Invalidate notes for a specific subject"""
        invalidate_cache_pattern(f'notes:subject:{subject_id}:*')


class CareersCache:
    """Cache helpers for Careers module"""
    
    @staticmethod
    def jobs_list_key(page: int = 1, **filters) -> str:
        """Generate cache key for jobs list"""
        return generate_cache_key('careers:jobs', page=page, **filters)
    
    @staticmethod
    def invalidate_jobs():
        """Invalidate all jobs list caches"""
        invalidate_cache_pattern('careers:jobs:*')


class AboutUsCache:
    """Cache helpers for About Us / Static Content"""
    
    @staticmethod
    def about_us_key() -> str:
        """Generate cache key for about us content"""
        return generate_cache_key('about_us')
    
    @staticmethod
    def invalidate_about_us():
        """Invalidate about us cache"""
        invalidate_cache(AboutUsCache.about_us_key())


# ============================================
# Session/Authentication Caching
# ============================================
class SessionCache:
    """Cache helpers for user sessions"""
    
    @staticmethod
    def user_session_key(user_id: int) -> str:
        """Generate cache key for user session"""
        return generate_cache_key('session:user', user_id)
    
    @staticmethod
    def invalidate_user_session(user_id: int):
        """Invalidate user session cache"""
        invalidate_cache(SessionCache.user_session_key(user_id))


# ============================================
# Utility Functions
# ============================================
def clear_all_cache() -> bool:
    """
    Clear entire cache - use with caution!
    Only use for development/testing or emergency cache flush
    """
    try:
        cache.clear()
        logger.warning("ENTIRE CACHE CLEARED - All cached data has been removed")
        return True
    except Exception as e:
        logger.error(f"Error clearing entire cache: {str(e)}")
        return False


def get_cache_stats() -> dict:
    """
    Get cache statistics if supported by backend
    """
    try:
        if hasattr(cache, 'get_stats'):
            return cache.get_stats()
        return {'message': 'Cache stats not available for this backend'}
    except Exception as e:
        logger.error(f"Error getting cache stats: {str(e)}")
        return {'error': str(e)}
