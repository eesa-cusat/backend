"""
Academics App Signals - Redis Cache Invalidation & Permission Groups Setup
Automatically invalidates cache when academic data is created, updated, or deleted
Creates permission groups after migrations
"""

from django.db.models.signals import post_save, post_delete, post_migrate
from django.dispatch import receiver
from django.contrib.auth.models import Group, Permission
from .models import Scheme, Subject, AcademicResource
from utils.redis_cache import AcademicsCache
import logging

logger = logging.getLogger(__name__)


# ==========================================
# CACHE INVALIDATION SIGNALS
# ==========================================

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


# ==========================================
# PERMISSION GROUPS AUTO-SETUP
# ==========================================

@receiver(post_migrate)
def create_permission_groups(sender, **kwargs):
    """
    Automatically create permission groups after migrations
    This ensures groups exist in production without manual command execution
    """
    # Only run for academics app
    if sender.name != 'academics':
        return
    
    print('\n🔐 Setting up EESA permission groups...')
    
    try:
        # Group 1: Events & Gallery Manager
        events_gallery_group, created = Group.objects.get_or_create(
            name='Events & Gallery Manager'
        )
        if created or not events_gallery_group.permissions.exists():
            events_perms = Permission.objects.filter(content_type__app_label='events')
            gallery_perms = Permission.objects.filter(content_type__app_label='gallery')
            events_gallery_group.permissions.set(list(events_perms) + list(gallery_perms))
            print(f'  ✓ {"Created" if created else "Updated"} Events & Gallery Manager')
        
        # Group 2: Academics & Projects Manager
        academics_projects_group, created = Group.objects.get_or_create(
            name='Academics & Projects Manager'
        )
        if created or not academics_projects_group.permissions.exists():
            academics_perms = Permission.objects.filter(content_type__app_label='academics')
            projects_perms = Permission.objects.filter(content_type__app_label='projects')
            academics_projects_group.permissions.set(list(academics_perms) + list(projects_perms))
            print(f'  ✓ {"Created" if created else "Updated"} Academics & Projects Manager')
        
        # Group 3: Careers & Placements Manager
        careers_placements_group, created = Group.objects.get_or_create(
            name='Careers & Placements Manager'
        )
        if created or not careers_placements_group.permissions.exists():
            careers_perms = Permission.objects.filter(content_type__app_label='careers')
            placements_perms = Permission.objects.filter(content_type__app_label='placements')
            careers_placements_group.permissions.set(list(careers_perms) + list(placements_perms))
            print(f'  ✓ {"Created" if created else "Updated"} Careers & Placements Manager')
        
        # Group 4: Teacher (all except accounts)
        teacher_group, created = Group.objects.get_or_create(name='Teacher')
        if created or not teacher_group.permissions.exists():
            all_perms = Permission.objects.exclude(
                content_type__app_label__in=['auth', 'accounts', 'contenttypes', 'sessions']
            )
            teacher_group.permissions.set(all_perms)
            print(f'  ✓ {"Created" if created else "Updated"} Teacher (all permissions except accounts)')
        
        # Group 5: Admin (full access)
        admin_group, created = Group.objects.get_or_create(name='Admin')
        if created or not admin_group.permissions.exists():
            all_perms = Permission.objects.all()
            admin_group.permissions.set(all_perms)
            print(f'  ✓ {"Created" if created else "Updated"} Admin (full access)')
        
        print('✅ Permission groups setup completed!\n')
        
    except Exception as e:
        print(f'⚠️  Error setting up permission groups: {e}\n')
