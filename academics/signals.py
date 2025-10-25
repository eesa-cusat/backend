"""
Academics App Signals - Redis Cache Invalidation
Automatically invalidates cache when academic data is created, updated, or deleted
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Scheme, Subject, AcademicResource
from utils.redis_cache import AcademicsCache
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Scheme)
@receiver(post_delete, sender=Scheme)
def invalidate_programs_cache_on_scheme_change(sender, instance, **kwargs):
    """Invalidate academic programs cache when schemes change"""
    try:
        AcademicsCache.invalidate_programs()
        logger.info(f"Scheme {instance.id} changed - programs cache invalidated")
    except Exception as e:
        logger.error(f"Error invalidating cache for scheme {instance.id}: {str(e)}")


@receiver(post_save, sender=Subject)
@receiver(post_delete, sender=Subject)
def invalidate_programs_cache_on_subject_change(sender, instance, **kwargs):
    """Invalidate academic programs cache when subjects change"""
    try:
        AcademicsCache.invalidate_programs()
        logger.info(f"Subject {instance.id} changed - programs cache invalidated")
    except Exception as e:
        logger.error(f"Error invalidating cache for subject {instance.id}: {str(e)}")


@receiver(post_save, sender=AcademicResource)
def invalidate_notes_cache_on_save(sender, instance, created, **kwargs):
    """Invalidate notes cache when a resource is created or updated"""
    try:
        if instance.subject:
            AcademicsCache.invalidate_notes_subject(instance.subject.id)
        action = "created" if created else "updated"
        logger.info(f"AcademicResource {instance.id} {action} - cache invalidated")
    except Exception as e:
        logger.error(f"Error invalidating cache for academic resource {instance.id}: {str(e)}")


@receiver(post_delete, sender=AcademicResource)
def invalidate_notes_cache_on_delete(sender, instance, **kwargs):
    """Invalidate notes cache when a resource is deleted"""
    try:
        if instance.subject:
            AcademicsCache.invalidate_notes_subject(instance.subject.id)
        logger.info(f"AcademicResource {instance.id} deleted - cache invalidated")
    except Exception as e:
        logger.error(f"Error invalidating cache for deleted academic resource {instance.id}: {str(e)}")
