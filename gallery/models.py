from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
from django.utils.text import slugify
import os

User = get_user_model()


def album_cover_upload_path(instance, filename):
    """Generate upload path for album cover images"""
    name, ext = os.path.splitext(filename)
    safe_name = "".join(c for c in instance.name if c.isalnum() or c in (' ', '-', '_')).rstrip()[:30]
    return f'gallery/covers/{safe_name.replace(" ", "_")}{ext}'


def photo_upload_path(instance, filename):
    """Generate upload path for gallery photos"""
    name, ext = os.path.splitext(filename)
    safe_album = "".join(c for c in instance.album.name if c.isalnum() or c in (' ', '-', '_')).rstrip()[:30]
    return f'gallery/albums/{safe_album.replace(" ", "_")}/{filename}'


class Album(models.Model):
    """
    Gallery Album - MVP Design
    Two types: EESA Programs (linked to events) and General Programs (standalone)
    """
    
    ALBUM_TYPES = [
        ('eesa', 'EESA Program'),
        ('general', 'General Program'),
        ('alumni', 'Alumni Batch'),
    ]
    
    # Core fields
    name = models.CharField(max_length=200)
    type = models.CharField(max_length=10, choices=ALBUM_TYPES)
    description = models.TextField(blank=True)
    cover_image = models.ImageField(
        upload_to=album_cover_upload_path,
        blank=True,
        null=True,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])]
    )
    
    # Event relation (nullable - only for EESA albums)
    event = models.OneToOneField(
        'events.Event',
        on_delete=models.CASCADE,
        related_name='album',
        blank=True,
        null=True,
        help_text="Link to event (required for EESA albums)"
    )
    
    # Alumni batch relation (nullable - only for Alumni albums)
    batch_year = models.PositiveIntegerField(
        blank=True,
        null=True,
        help_text="Graduation year for alumni albums (required for Alumni albums)"
    )
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['type']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.name} ({self.get_type_display()})"
    
    def save(self, *args, **kwargs):
        # Auto-set name for EESA albums
        if self.type == 'eesa' and self.event and not self.name:
            self.name = self.event.title
        
        # Auto-set name for Alumni albums
        if self.type == 'alumni' and self.batch_year and not self.name:
            self.name = f"Batch {self.batch_year}"
        
        super().save(*args, **kwargs)
    
    def clean(self):
        from django.core.exceptions import ValidationError
        
        # EESA albums must be linked to an event
        if self.type == 'eesa' and not self.event:
            raise ValidationError("EESA albums must be linked to an event.")
        
        # General albums cannot be linked to events or batches
        if self.type == 'general' and self.event:
            raise ValidationError("General albums cannot be linked to events.")
        if self.type == 'general' and self.batch_year:
            raise ValidationError("General albums cannot have batch years.")
        
        # Alumni albums must have batch year and cannot be linked to events
        if self.type == 'alumni' and not self.batch_year:
            raise ValidationError("Alumni albums must have a batch year.")
        if self.type == 'alumni' and self.event:
            raise ValidationError("Alumni albums cannot be linked to events.")
    
    @property
    def photo_count(self):
        return self.photos.count()


class Photo(models.Model):
    """
    Gallery Photo - MVP Design
    Always belongs to an album
    """
    
    # Core fields
    album = models.ForeignKey(Album, on_delete=models.CASCADE, related_name='photos')
    image = models.ImageField(
        upload_to=photo_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'webp'])]
    )
    caption = models.TextField(blank=True)
    
    # Metadata
    uploaded_at = models.DateTimeField(auto_now_add=True)
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-uploaded_at']
        indexes = [
            models.Index(fields=['album', 'uploaded_at']),
        ]
    
    def __str__(self):
        return f"Photo in {self.album.name} - {self.uploaded_at.strftime('%Y-%m-%d')}"
