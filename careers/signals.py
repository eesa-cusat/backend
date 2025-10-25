"""
Careers App Signals - Redis Cache Invalidation
Automatically invalidates cache when careers data is created, updated, or deleted
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import JobOpportunity, InternshipOpportunity, CertificateOpportunity
from utils.redis_cache import CareersCache
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=JobOpportunity)
@receiver(post_delete, sender=JobOpportunity)
def invalidate_jobs_cache(sender, instance, **kwargs):
    """Invalidate jobs cache when a job is created, updated, or deleted"""
    try:
        CareersCache.invalidate_jobs()
        logger.info(f"JobOpportunity {instance.id} changed - cache invalidated")
    except Exception as e:
        logger.error(f"Error invalidating cache for job {instance.id}: {str(e)}")


@receiver(post_save, sender=InternshipOpportunity)
@receiver(post_delete, sender=InternshipOpportunity)
def invalidate_internships_cache(sender, instance, **kwargs):
    """Invalidate internships cache when an internship is created, updated, or deleted"""
    try:
        # Using jobs cache pattern for internships too
        CareersCache.invalidate_jobs()
        logger.info(f"InternshipOpportunity {instance.id} changed - cache invalidated")
    except Exception as e:
        logger.error(f"Error invalidating cache for internship {instance.id}: {str(e)}")


@receiver(post_save, sender=CertificateOpportunity)
@receiver(post_delete, sender=CertificateOpportunity)
def invalidate_certificates_cache(sender, instance, **kwargs):
    """Invalidate certificates cache when a certificate is created, updated, or deleted"""
    try:
        CareersCache.invalidate_jobs()
        logger.info(f"CertificateOpportunity {instance.id} changed - cache invalidated")
    except Exception as e:
        logger.error(f"Error invalidating cache for certificate {instance.id}: {str(e)}")
