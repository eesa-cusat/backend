from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


def project_report_upload_path(instance, filename):
    """Generate upload path for project reports"""
    import os
    name, ext = os.path.splitext(filename)
    safe_title = "".join(c for c in instance.title if c.isalnum() or c in (' ', '-', '_')).rstrip()[:25]
    category = instance.category.replace('_', '-')
    return f'projects/{category}/reports/{safe_title.replace(" ", "_")}{ext}'


def project_thumbnail_upload_path(instance, filename):
    """Generate upload path for project thumbnails"""
    import os
    name, ext = os.path.splitext(filename)
    safe_title = "".join(c for c in instance.title if c.isalnum() or c in (' ', '-', '_')).rstrip()[:25]
    category = instance.category.replace('_', '-')
    return f'projects/{category}/thumbnails/{safe_title.replace(" ", "_")}{ext}'


def project_image_upload_path(instance, filename):
    """Generate upload path for project main images"""
    import os
    name, ext = os.path.splitext(filename)
    safe_title = "".join(c for c in instance.title if c.isalnum() or c in (' ', '-', '_')).rstrip()[:25]
    category = instance.category.replace('_', '-')
    return f'projects/{category}/images/{safe_title.replace(" ", "_")}{ext}'


def project_gallery_upload_path(instance, filename):
    """Generate upload path for project gallery images"""
    import os
    name, ext = os.path.splitext(filename)
    safe_title = "".join(c for c in instance.project.title if c.isalnum() or c in (' ', '-', '_')).rstrip()[:25]
    category = instance.project.category.replace('_', '-')
    return f'projects/{category}/gallery/{safe_title.replace(" ", "_")}/{filename}'


class Project(models.Model):
    """Projects showcase - managed by staff only"""
    
    CATEGORY_CHOICES = [
        ('web_development', 'Web Development'),
        ('mobile_app', 'Mobile App'),
        ('machine_learning', 'Machine Learning'),
        ('iot', 'Internet of Things'),
        ('robotics', 'Robotics'),
        ('embedded_systems', 'Embedded Systems'),
        ('data_science', 'Data Science'),
        ('cybersecurity', 'Cybersecurity'),
        ('blockchain', 'Blockchain'),
        ('ai', 'Artificial Intelligence'),
        ('other', 'Other'),
    ]
    
    title = models.CharField(max_length=200)
    description = models.TextField()
    abstract = models.TextField(blank=True, null=True, help_text="Project abstract or summary")
    category = models.CharField(max_length=30, choices=CATEGORY_CHOICES)
    
    # Academic Information
    student_batch = models.CharField(max_length=20, blank=True, null=True, help_text="e.g., 2021-2025")
    academic_year = models.CharField(max_length=10, blank=True, null=True, help_text="e.g., 2024, 2023")
    
    # Media Files
    thumbnail = models.ImageField(
        upload_to=project_thumbnail_upload_path,
        blank=True,
        null=True,
        help_text="Thumbnail image for project cards and listings (recommended: 800x600px)"
    )
    project_image = models.ImageField(
        upload_to=project_image_upload_path,
        blank=True,
        null=True,
        help_text="Main project image for detailed view (fallback if thumbnail not provided)"
    )
    project_report = models.FileField(
        upload_to=project_report_upload_path, 
        blank=True, 
        null=True, 
        help_text="Upload project report (PDF/DOC/DOCX). Maximum file size: 15MB."
    )
    
    # Links
    github_url = models.URLField(blank=True, null=True)
    demo_url = models.URLField(blank=True, null=True)
    
    # Project management (only staff can create/edit)
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_projects')
    is_featured = models.BooleanField(default=False, help_text="Feature this project on homepage")
    is_published = models.BooleanField(default=True, help_text="Make this project visible to public")
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Project"
        verbose_name_plural = "Projects"
        ordering = ['-is_featured', '-created_at']
        indexes = [
            models.Index(fields=['category']),
            models.Index(fields=['created_by']),
            models.Index(fields=['is_featured', 'is_published']),
            models.Index(fields=['created_at']),
            models.Index(fields=['student_batch']),
            models.Index(fields=['academic_year']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.get_category_display()}"
    
    @property
    def team_count(self):
        """Get total team size including creator"""
        return self.team_members.count() + 1  # +1 for creator
    
    @property 
    def created_by_name(self):
        """Get creator's full name"""
        return self.created_by.get_full_name() or self.created_by.username
    
    @property
    def thumbnail_url(self):
        """Get thumbnail URL with fallback to project_image"""
        if self.thumbnail:
            return self.thumbnail.url if hasattr(self.thumbnail, 'url') else None
        elif self.project_image:
            return self.project_image.url if hasattr(self.project_image, 'url') else None
        # Fallback to first gallery image
        first_image = self.images.first()
        if first_image and first_image.image:
            return first_image.image.url if hasattr(first_image.image, 'url') else None
        return None
    
    @property
    def report_file_type(self):
        """Get the MIME type for the project report"""
        if not self.project_report:
            return None
        
        filename = self.project_report.name.lower()
        if filename.endswith('.pdf'):
            return 'application/pdf'
        elif filename.endswith('.docx'):
            return 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        elif filename.endswith('.doc'):
            return 'application/msword'
        return 'application/octet-stream'
    
    @property
    def featured_video(self):
        """Get the featured video for this project"""
        featured = self.videos.filter(is_featured=True).first()
        return featured if featured else self.videos.first()


class TeamMember(models.Model):
    """Team members for projects"""
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='team_members')
    name = models.CharField(max_length=200)
    linkedin_url = models.URLField(max_length=500, blank=True, null=True)
    role = models.CharField(max_length=200, blank=True, null=True, help_text="e.g., Frontend Developer, UI Designer")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['name']
        indexes = [
            models.Index(fields=['project', 'name']),
        ]
    
    def __str__(self):
        return f"{self.name} - {self.project.title}"


class ProjectImage(models.Model):
    """Project images for gallery"""
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='images')
    image = models.ImageField(upload_to=project_gallery_upload_path, help_text="Upload project image")
    caption = models.CharField(max_length=500, blank=True, null=True)
    is_featured = models.BooleanField(default=False, help_text="Show as main project image")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-is_featured', 'created_at']
        indexes = [
            models.Index(fields=['project', 'is_featured']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.project.title} - Image {self.id}"


class ProjectVideo(models.Model):
    """Project videos for demonstration"""
    
    project = models.ForeignKey(Project, on_delete=models.CASCADE, related_name='videos')
    video_url = models.URLField(help_text="YouTube, Vimeo, or direct video URL")
    title = models.CharField(max_length=200, blank=True, null=True)
    description = models.TextField(blank=True, null=True)
    is_featured = models.BooleanField(default=False, help_text="Show as main project video")
    
    created_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        ordering = ['-is_featured', 'created_at']
        indexes = [
            models.Index(fields=['project', 'is_featured']),
            models.Index(fields=['created_at']),
        ]
    
    def __str__(self):
        return f"{self.project.title} - {self.title or 'Video'}"
