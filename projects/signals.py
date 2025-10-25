"""
Projects App Signals - Redis Cache Invalidation
Automatically invalidates cache when project data is created, updated, or deleted
"""

from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Project, ProjectImage, ProjectVideo, TeamMember
from utils.redis_cache import ProjectsCache
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Project)
def invalidate_project_cache_on_save(sender, instance, created, **kwargs):
    """
    Invalidate projects cache when a project is created or updated
    """
    try:
        # Invalidate project detail cache
        ProjectsCache.invalidate_project(instance.id)
        
        # Invalidate projects list cache
        ProjectsCache.invalidate_projects_list()
        
        action = "created" if created else "updated"
        logger.info(f"Project {instance.id} {action} - cache invalidated")
    except Exception as e:
        logger.error(f"Error invalidating cache for project {instance.id}: {str(e)}")


@receiver(post_delete, sender=Project)
def invalidate_project_cache_on_delete(sender, instance, **kwargs):
    """
    Invalidate projects cache when a project is deleted
    """
    try:
        # Invalidate project detail cache
        ProjectsCache.invalidate_project(instance.id)
        
        # Invalidate projects list cache
        ProjectsCache.invalidate_projects_list()
        
        logger.info(f"Project {instance.id} deleted - cache invalidated")
    except Exception as e:
        logger.error(f"Error invalidating cache for deleted project {instance.id}: {str(e)}")


@receiver(post_save, sender=ProjectImage)
@receiver(post_delete, sender=ProjectImage)
def invalidate_project_cache_on_image_change(sender, instance, **kwargs):
    """
    Invalidate project cache when images are added/updated/deleted
    """
    try:
        if instance.project:
            ProjectsCache.invalidate_project(instance.project.id)
            logger.info(f"Project {instance.project.id} image updated - cache invalidated")
    except Exception as e:
        logger.error(f"Error invalidating cache for project image: {str(e)}")


@receiver(post_save, sender=ProjectVideo)
@receiver(post_delete, sender=ProjectVideo)
def invalidate_project_cache_on_video_change(sender, instance, **kwargs):
    """
    Invalidate project cache when videos are added/updated/deleted
    """
    try:
        if instance.project:
            ProjectsCache.invalidate_project(instance.project.id)
            logger.info(f"Project {instance.project.id} video updated - cache invalidated")
    except Exception as e:
        logger.error(f"Error invalidating cache for project video: {str(e)}")


@receiver(post_save, sender=TeamMember)
@receiver(post_delete, sender=TeamMember)
def invalidate_project_cache_on_team_change(sender, instance, **kwargs):
    """
    Invalidate project cache when team members are added/updated/deleted
    """
    try:
        if instance.project:
            ProjectsCache.invalidate_project(instance.project.id)
            logger.info(f"Project {instance.project.id} team member updated - cache invalidated")
    except Exception as e:
        logger.error(f"Error invalidating cache for project team member: {str(e)}")
