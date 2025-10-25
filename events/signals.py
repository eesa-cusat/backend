from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import Event, EventRegistration, EventSpeaker, EventSchedule
from gallery.models import Album
from utils.redis_cache import EventsCache
import os
from django.core.files.base import ContentFile
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=Event)
def create_event_album(sender, instance, created, **kwargs):
    """
    Automatically create a gallery album when an event is created.
    Uses event flyer as the album cover image.
    Also invalidates event cache.
    """
    # Invalidate cache on event create/update
    try:
        EventsCache.invalidate_event(instance.id)
        EventsCache.invalidate_events_list()
        action = "created" if created else "updated"
        logger.info(f"Event {instance.id} {action} - cache invalidated")
    except Exception as e:
        logger.error(f"Error invalidating cache for event {instance.id}: {str(e)}")
    
    if created and instance.status == 'published':
        try:
            # Check if album already exists for this event
            if not hasattr(instance, 'album') or not instance.album:
                # Create album with event details
                album = Album.objects.create(
                    name=instance.title,
                    type='eesa',
                    description=f"Photo gallery for {instance.title}",
                    event=instance,
                    created_by=instance.created_by
                )
                
                # If event has a flyer, copy it as album cover
                if instance.event_flyer:
                    try:
                        # Get the flyer file
                        flyer_file = instance.event_flyer
                        
                        # Create a new file name for the album cover
                        file_name = os.path.basename(flyer_file.name)
                        name, ext = os.path.splitext(file_name)
                        cover_name = f"album_cover_{name}{ext}"
                        
                        # Copy the flyer content to album cover
                        flyer_file.seek(0)  # Reset file pointer
                        album.cover_image.save(
                            cover_name,
                            ContentFile(flyer_file.read()),
                            save=True
                        )
                        
                        print(f"✅ Created album '{album.name}' for event '{instance.title}' with cover image")
                    except Exception as e:
                        print(f"⚠️ Created album '{album.name}' for event '{instance.title}' but failed to copy cover image: {e}")
                else:
                    print(f"✅ Created album '{album.name}' for event '{instance.title}' (no flyer to use as cover)")
                
        except Exception as e:
            print(f"❌ Failed to create album for event '{instance.title}': {e}")


@receiver(post_save, sender=Event)
def update_event_album(sender, instance, created, **kwargs):
    """
    Update the album when event details change.
    """
    if not created and hasattr(instance, 'album') and instance.album:
        try:
            album = instance.album
            
            # Update album name if event title changed
            if album.name != instance.title:
                album.name = instance.title
                album.save()
                
            # Update description
            expected_description = f"Photo gallery for {instance.title}"
            if album.description != expected_description:
                album.description = expected_description
                album.save()
                
            print(f"✅ Updated album '{album.name}' for event '{instance.title}'")
        except Exception as e:
            print(f"❌ Failed to update album for event '{instance.title}': {e}")


@receiver(post_delete, sender=Event)
def invalidate_event_cache_on_delete(sender, instance, **kwargs):
    """Invalidate events cache when an event is deleted"""
    try:
        EventsCache.invalidate_event(instance.id)
        EventsCache.invalidate_events_list()
        logger.info(f"Event {instance.id} deleted - cache invalidated")
    except Exception as e:
        logger.error(f"Error invalidating cache for deleted event {instance.id}: {str(e)}")


@receiver(post_save, sender=EventRegistration)
def invalidate_event_cache_on_registration(sender, instance, created, **kwargs):
    """Invalidate event cache when someone registers"""
    try:
        if instance.event:
            EventsCache.invalidate_event(instance.event.id)
            logger.info(f"Event {instance.event.id} registration updated - cache invalidated")
    except Exception as e:
        logger.error(f"Error invalidating cache for event registration: {str(e)}")


@receiver(post_save, sender=EventSpeaker)
@receiver(post_delete, sender=EventSpeaker)
def invalidate_event_cache_on_speaker_change(sender, instance, **kwargs):
    """Invalidate event cache when speakers are added/updated/deleted"""
    try:
        if instance.event:
            EventsCache.invalidate_event(instance.event.id)
            logger.info(f"Event {instance.event.id} speaker updated - cache invalidated")
    except Exception as e:
        logger.error(f"Error invalidating cache for event speaker: {str(e)}")


@receiver(post_save, sender=EventSchedule)
@receiver(post_delete, sender=EventSchedule)
def invalidate_event_cache_on_schedule_change(sender, instance, **kwargs):
    """Invalidate event cache when schedule is added/updated/deleted"""
    try:
        if instance.event:
            EventsCache.invalidate_event(instance.event.id)
            logger.info(f"Event {instance.event.id} schedule updated - cache invalidated")
    except Exception as e:
        logger.error(f"Error invalidating cache for event schedule: {str(e)}")

