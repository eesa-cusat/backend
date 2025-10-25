from django.db.models.signals import post_save, post_delete
from django.dispatch import receiver
from .models import AlumniBatch, Alumni
from gallery.models import Album, Photo
from utils.redis_cache import AlumniCache
import os
from django.core.files.base import ContentFile
import logging

logger = logging.getLogger(__name__)


@receiver(post_save, sender=AlumniBatch)
def add_batch_to_alumni_album(sender, instance, created, **kwargs):
    """
    Add batch photo to the single 'Alumni' album when an AlumniBatch is created.
    Creates the alumni album if it doesn't exist.
    Also invalidates cache.
    """
    # Invalidate cache
    try:
        AlumniCache.invalidate_batches()
        action = "created" if created else "updated"
        logger.info(f"AlumniBatch {instance.id} {action} - cache invalidated")
    except Exception as e:
        logger.error(f"Error invalidating cache for alumni batch {instance.id}: {str(e)}")
    
    if created and instance.batch_group_photo:
        try:
            # Get or create the single Alumni album
            album, album_created = Album.objects.get_or_create(
                name="Alumni",
                type='general',  # Changed from 'alumni' to 'general' since it's not batch-specific
                defaults={
                    'description': "Photo gallery for all alumni batches",
                    'created_by': None  # System created
                }
            )
            
            if album_created:
                print(f"✅ Created main Alumni album")
            
            # Add batch group photo to the album
            try:
                photo_file = instance.batch_group_photo
                file_name = os.path.basename(photo_file.name)
                name, ext = os.path.splitext(file_name)
                
                # Create photo with batch year as caption
                photo = Photo.objects.create(
                    album=album,
                    caption=f"{instance.batch_name} - Graduation Photo",
                    uploaded_by=None  # System created
                )
                
                # Save the photo
                photo_name = f"batch_{instance.graduation_year or 'unknown'}_group{ext}"
                photo_file.seek(0)  # Reset file pointer
                photo.image.save(
                    photo_name,
                    ContentFile(photo_file.read()),
                    save=True
                )
                
                # Set as album cover if it's the first photo
                if album.photo_count == 1 and not album.cover_image:
                    photo_file.seek(0)  # Reset file pointer
                    cover_name = f"alumni_cover{ext}"
                    album.cover_image.save(
                        cover_name,
                        ContentFile(photo_file.read()),
                        save=True
                    )
                
                print(f"✅ Added batch photo for '{instance.batch_name}' to Alumni album")
                
            except Exception as e:
                print(f"⚠️ Failed to add batch photo for '{instance.batch_name}': {e}")
                
        except Exception as e:
            print(f"❌ Failed to process alumni album for batch '{instance.batch_name}': {e}")
    elif created:
        print(f"ℹ️ Batch '{instance.batch_name}' created without group photo - not added to Alumni album")


@receiver(post_save, sender=AlumniBatch)
def update_batch_photo_in_alumni_album(sender, instance, created, **kwargs):
    """
    Update batch photo in the Alumni album when batch details change.
    """
    if not created and instance.batch_group_photo:
        try:
            # Get the Alumni album
            album = Album.objects.filter(
                name="Alumni",
                type='general'
            ).first()
            
            if not album:
                # Create Alumni album if it doesn't exist
                album = Album.objects.create(
                    name="Alumni",
                    type='general',
                    description="Photo gallery for all alumni batches",
                    created_by=None
                )
                print(f"✅ Created Alumni album")
            
            # Check if a photo for this batch already exists
            existing_photo = Photo.objects.filter(
                album=album,
                caption__icontains=instance.batch_name
            ).first()
            
            if existing_photo:
                # Update existing photo
                try:
                    photo_file = instance.batch_group_photo
                    file_name = os.path.basename(photo_file.name)
                    name, ext = os.path.splitext(file_name)
                    
                    photo_name = f"batch_{instance.graduation_year or 'unknown'}_group{ext}"
                    photo_file.seek(0)
                    
                    # Update the existing photo
                    existing_photo.image.save(
                        photo_name,
                        ContentFile(photo_file.read()),
                        save=True
                    )
                    existing_photo.caption = f"{instance.batch_name} - Graduation Photo"
                    existing_photo.save()
                    
                    print(f"✅ Updated batch photo for '{instance.batch_name}' in Alumni album")
                except Exception as e:
                    print(f"⚠️ Failed to update batch photo for '{instance.batch_name}': {e}")
            else:
                # Add new photo if it doesn't exist
                try:
                    photo_file = instance.batch_group_photo
                    file_name = os.path.basename(photo_file.name)
                    name, ext = os.path.splitext(file_name)
                    
                    photo = Photo.objects.create(
                        album=album,
                        caption=f"{instance.batch_name} - Graduation Photo",
                        uploaded_by=None
                    )
                    
                    photo_name = f"batch_{instance.graduation_year or 'unknown'}_group{ext}"
                    photo_file.seek(0)
                    photo.image.save(
                        photo_name,
                        ContentFile(photo_file.read()),
                        save=True
                    )
                    
                    # Set as cover if it's the first photo
                    if album.photo_count == 1 and not album.cover_image:
                        photo_file.seek(0)
                        cover_name = f"alumni_cover{ext}"
                        album.cover_image.save(
                            cover_name,
                            ContentFile(photo_file.read()),
                            save=True
                        )
                    
                    print(f"✅ Added new batch photo for '{instance.batch_name}' to Alumni album")
                except Exception as e:
                    print(f"⚠️ Failed to add batch photo for '{instance.batch_name}': {e}")
                    
        except Exception as e:
            print(f"❌ Failed to process Alumni album update for batch '{instance.batch_name}': {e}")


@receiver(post_delete, sender=AlumniBatch)
def invalidate_batch_cache_on_delete(sender, instance, **kwargs):
    """Invalidate alumni batches cache when a batch is deleted"""
    try:
        AlumniCache.invalidate_batches()
        if instance.batch_year_range:
            AlumniCache.invalidate_batch_students(instance.batch_year_range)
        logger.info(f"AlumniBatch {instance.id} deleted - cache invalidated")
    except Exception as e:
        logger.error(f"Error invalidating cache for deleted alumni batch {instance.id}: {str(e)}")


@receiver(post_save, sender=Alumni)
def invalidate_alumni_cache_on_save(sender, instance, created, **kwargs):
    """Invalidate alumni cache when an alumni record is created or updated"""
    try:
        if instance.batch and instance.batch.batch_year_range:
            AlumniCache.invalidate_batch_students(instance.batch.batch_year_range)
        AlumniCache.invalidate_batches()
        action = "created" if created else "updated"
        logger.info(f"Alumni {instance.id} {action} - cache invalidated")
    except Exception as e:
        logger.error(f"Error invalidating cache for alumni {instance.id}: {str(e)}")


@receiver(post_delete, sender=Alumni)
def invalidate_alumni_cache_on_delete(sender, instance, **kwargs):
    """Invalidate alumni cache when an alumni record is deleted"""
    try:
        if instance.batch and instance.batch.batch_year_range:
            AlumniCache.invalidate_batch_students(instance.batch.batch_year_range)
        AlumniCache.invalidate_batches()
        logger.info(f"Alumni {instance.id} deleted - cache invalidated")
    except Exception as e:
        logger.error(f"Error invalidating cache for deleted alumni {instance.id}: {str(e)}")

