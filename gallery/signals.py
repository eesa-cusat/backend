"""
Gallery App Signals - Redis Cache Invalidation
Automatically invalidates cache when gallery data is created, updated, or deleted
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Album, Photo
from utils.redis_cache import GalleryCache
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Album)
def invalidate_album_cache_on_save(sender, instance, created, **kwargs):
    """
    Invalidate gallery cache when an album is created or updated
    """
    try:
        # Invalidate album detail cache
        GalleryCache.invalidate_album(instance.id)
        
        # Invalidate albums list cache for the specific type
        GalleryCache.invalidate_albums(instance.type)
        
        # Also invalidate 'all' albums list
        GalleryCache.invalidate_albums()
        
        action = "created" if created else "updated"
        logger.info(f"Album {instance.id} {action} - cache invalidated")
    except Exception as e:
        logger.error(f"Error invalidating cache for album {instance.id}: {str(e)}")


@receiver(post_delete, sender=Album)
def invalidate_album_cache_on_delete(sender, instance, **kwargs):
    """
    Invalidate gallery cache when an album is deleted
    """
    try:
        # Invalidate album detail cache
        GalleryCache.invalidate_album(instance.id)
        
        # Invalidate albums list cache
        GalleryCache.invalidate_albums(instance.type)
        GalleryCache.invalidate_albums()
        
        logger.info(f"Album {instance.id} deleted - cache invalidated")
    except Exception as e:
        logger.error(f"Error invalidating cache for deleted album {instance.id}: {str(e)}")


@receiver(post_save, sender=Photo)
def invalidate_photo_cache_on_save(sender, instance, created, **kwargs):
    """
    Invalidate gallery cache when a photo is created or updated
    """
    try:
        # Invalidate the album detail cache (photos are nested in album)
        if instance.album:
            GalleryCache.invalidate_album(instance.album.id)
            logger.info(f"Photo {instance.id} {'added to' if created else 'updated in'} album {instance.album.id} - cache invalidated")
    except Exception as e:
        logger.error(f"Error invalidating cache for photo {instance.id}: {str(e)}")


@receiver(post_delete, sender=Photo)
def invalidate_photo_cache_on_delete(sender, instance, **kwargs):
    """
    Invalidate gallery cache when a photo is deleted
    """
    try:
        # Invalidate the album detail cache
        if instance.album:
            GalleryCache.invalidate_album(instance.album.id)
            logger.info(f"Photo {instance.id} deleted from album {instance.album.id} - cache invalidated")
    except Exception as e:
        logger.error(f"Error invalidating cache for deleted photo {instance.id}: {str(e)}")
