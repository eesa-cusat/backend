from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
import os

User = get_user_model()

def gallery_image_upload_path(instance, filename):
    """Generate upload path for gallery images"""
    name, ext = os.path.splitext(filename)
    safe_category = "".join(c for c in instance.album.category.name if c.isalnum() or c in (' ', '-', '_')).rstrip()[:20]
    safe_album = "".join(c for c in instance.album.name if c.isalnum() or c in (' ', '-', '_')).rstrip()[:20]
    return f'gallery/{safe_category.replace(" ", "_")}/{safe_album.replace(" ", "_")}/{filename}'

def gallery_thumbnail_upload_path(instance, filename):
    """Generate upload path for gallery thumbnails"""
    name, ext = os.path.splitext(filename)
    safe_category = "".join(c for c in instance.album.category.name if c.isalnum() or c in (' ', '-', '_')).rstrip()[:20]
    return f'gallery/thumbnails/{safe_category.replace(" ", "_")}/{filename}'

class GalleryCategory(models.Model):
    """Predefined categories for organizing gallery images"""
    
    CATEGORY_CHOICES = [
        ('events', 'Events Photos'),
        ('iv_photos', 'IV Photos'),
        ('tech_fest', 'Tech Fest Photos'),
        ('alumni', 'Alumni Photos'),
        ('dept_photos', 'Department Photos'),
    ]
    
    name = models.CharField(max_length=100, unique=True)
    category_type = models.CharField(max_length=20, choices=CATEGORY_CHOICES, unique=True)
    description = models.TextField(blank=True)
    slug = models.SlugField(max_length=100, unique=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Icon class name")
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Gallery Categories"
        ordering = ['display_order', 'name']
        
    def __str__(self):
        return self.name
    
    def save(self, *args, **kwargs):
        """Auto-set name and slug based on category type"""
        if not self.pk:  # Only for new instances
            if self.category_type == 'events':
                self.name = 'Events Photos'
                self.slug = 'events-photos'
            elif self.category_type == 'iv_photos':
                self.name = 'IV Photos'
                self.slug = 'iv-photos'
            elif self.category_type == 'tech_fest':
                self.name = 'Tech Fest Photos'
                self.slug = 'tech-fest-photos'
            elif self.category_type == 'alumni':
                self.name = 'Alumni Photos'
                self.slug = 'alumni-photos'
            elif self.category_type == 'dept_photos':
                self.name = 'Department Photos'
                self.slug = 'department-photos'
        super().save(*args, **kwargs)
    
    @property
    def album_count(self):
        return self.albums.filter(is_active=True).count()
    
    @property
    def total_images(self):
        return sum(album.image_count for album in self.albums.filter(is_active=True))


class GalleryAlbum(models.Model):
    """Album for grouping related images within a category"""
    name = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    slug = models.SlugField(max_length=200)
    category = models.ForeignKey(GalleryCategory, on_delete=models.CASCADE, related_name='albums')
    cover_image = models.ForeignKey(
        'GalleryImage', 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='cover_for_albums'
    )
    
    # Album details
    event_date = models.DateField(blank=True, null=True)
    location = models.CharField(max_length=200, blank=True)
    
    # Settings
    is_active = models.BooleanField(default=True)
    is_public = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    display_order = models.IntegerField(default=0)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_featured', '-display_order', '-created_at']
        unique_together = ['slug', 'category']  # Same slug can exist in different categories
        
    def __str__(self):
        return f"{self.name} ({self.category.name})"
    
    @property
    def image_count(self):
        return self.images.filter(is_public=True).count()


class GalleryImage(models.Model):
    """Model for gallery images - always belongs to an album"""
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    image = models.ImageField(
        upload_to=gallery_image_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=['jpg', 'jpeg', 'png', 'gif', 'webp'])]
    )
    thumbnail = models.ImageField(upload_to=gallery_thumbnail_upload_path, blank=True, null=True)
    
    # Organization - Image belongs to an album
    album = models.ForeignKey(GalleryAlbum, on_delete=models.CASCADE, related_name='images')
    tags = models.CharField(max_length=500, blank=True, help_text="Comma-separated tags")
    
    # Image details
    photographer = models.CharField(max_length=100, blank=True)
    camera_info = models.CharField(max_length=200, blank=True)
    
    # Display settings
    is_featured = models.BooleanField(default=False)
    is_public = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    
    # Metadata
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    file_size = models.BigIntegerField(blank=True, null=True)  # in bytes
    image_width = models.IntegerField(blank=True, null=True)
    image_height = models.IntegerField(blank=True, null=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_featured', '-display_order', '-created_at']
        
    def __str__(self):
        return self.title
    
    def save(self, *args, **kwargs):
        # Set file size if image exists and file is accessible
        if self.image:
            try:
                self.file_size = self.image.size
            except (FileNotFoundError, OSError):
                # Handle case where image file doesn't exist (e.g., placeholder/test data)
                if not self.file_size:
                    self.file_size = 0
        super().save(*args, **kwargs)
    
    @property
    def file_size_mb(self):
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0
    
    @property
    def tag_list(self):
        if self.tags:
            return [tag.strip() for tag in self.tags.split(',') if tag.strip()]
        return []
    
    @property
    def category(self):
        """Get category through album"""
        return self.album.category
    
    @property
    def event_name(self):
        """Get event name from album"""
        return self.album.name
    
    @property
    def event_date(self):
        """Get event date from album"""
        return self.album.event_date
    
    @property
    def location(self):
        """Get location from album"""
        return self.album.location
