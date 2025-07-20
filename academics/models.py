from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
# from students.models import Student  # Temporarily disabled during migration

User = get_user_model()


class Scheme(models.Model):
    """Academic scheme model (2018, 2022, etc.)"""
    
    year = models.PositiveIntegerField(unique=True)
    name = models.CharField(max_length=100, help_text="e.g., 'Scheme 2018', 'CBCS 2022'")
    description = models.TextField(blank=True, null=True)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-year']
        
    def __str__(self):
        return f"{self.name} ({self.year})"


class Subject(models.Model):
    """Subject model structured as Scheme → Semester → Subject"""
    
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20)
    scheme = models.ForeignKey(Scheme, on_delete=models.CASCADE, related_name='subjects')
    semester = models.PositiveIntegerField()
    credits = models.PositiveIntegerField(default=3)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['code', 'scheme', 'semester']
        ordering = ['scheme__year', 'semester', 'name']
        indexes = [
            models.Index(fields=['scheme', 'semester']),
            models.Index(fields=['code']),
        ]
    
    def __str__(self):
        return f"{self.code} - {self.name} ({self.scheme.name} Sem{self.semester})"
    
    @property
    def scheme_year(self):
        """Get scheme year"""
        return self.scheme.year


class AcademicCategory(models.Model):
    """Fixed categories for academic resources - only 3 types needed"""
    
    CATEGORY_TYPES = [
        ('notes', 'Notes'),
        ('textbook', 'Textbooks'),
        ('pyq', 'Previous Year Questions'),
        ('regulations', 'Regulations'),
        ('syllabus', 'Syllabus'),
    ]
    
    name = models.CharField(max_length=100)
    slug = models.SlugField(max_length=100, unique=True)
    category_type = models.CharField(max_length=20, choices=CATEGORY_TYPES)
    description = models.TextField(blank=True)
    icon = models.CharField(max_length=50, blank=True, help_text="Icon class name")
    is_active = models.BooleanField(default=True)
    display_order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name_plural = "Academic Categories"
        ordering = ['display_order', 'name']
        
    def __str__(self):
        return f"{self.get_category_type_display()}"
    
    def save(self, *args, **kwargs):
        """Ensure only 5 categories exist"""
        if not self.pk:  # Only for new instances
            if self.category_type == 'notes':
                self.name = 'Notes'
                self.slug = 'notes'
            elif self.category_type == 'textbook':
                self.name = 'Textbooks'
                self.slug = 'textbooks'
            elif self.category_type == 'pyq':
                self.name = 'Previous Year Questions'
                self.slug = 'pyq'
            elif self.category_type == 'regulations':
                self.name = 'Regulations'
                self.slug = 'regulations'
            elif self.category_type == 'syllabus':
                self.name = 'Syllabus'
                self.slug = 'syllabus'
        super().save(*args, **kwargs)


def academic_resource_upload_path(instance, filename):
    """Generate upload path for academic resources"""
    return f"academics/{instance.category.category_type}/{instance.subject.scheme.year}/{instance.subject.semester}/{instance.subject.code}/{filename}"


class AcademicResource(models.Model):
    """Unified model for notes, textbooks, and PYQ"""
    
    MODULE_CHOICES = [
        (1, 'Module 1'),
        (2, 'Module 2'),
        (3, 'Module 3'),
        (4, 'Module 4'),
        (5, 'Module 5'),
        (0, 'General/Complete'),
    ]
    
    EXAM_TYPE_CHOICES = [
        ('internal', 'Internal Exam'),
        ('sem', 'Semester Exam'),
        ('other', 'Other'),
    ]
    
    # Basic Information
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.ForeignKey(AcademicCategory, on_delete=models.CASCADE, related_name='resources')
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='resources')
    
    # File Information
    file = models.FileField(
        upload_to=academic_resource_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
        help_text="Upload only PDF files. Maximum file size: 15MB. Only PDF format is supported for academic resources."
    )
    file_size = models.BigIntegerField(blank=True, null=True)  # in bytes

    def clean(self):
        super().clean()
        if self.file:
            # Check file extension
            if not self.file.name.lower().endswith('.pdf'):
                from django.core.exceptions import ValidationError
                raise ValidationError({'file': 'Only PDF files are allowed. Please upload a PDF document.'})
            
            # Check file size (15MB limit)
            if self.file.size > 15 * 1024 * 1024:
                from django.core.exceptions import ValidationError
                raise ValidationError({'file': 'File size must be less than 15MB. Please compress the file or use a smaller document.'})
    
    # Resource-specific fields
    module_number = models.PositiveIntegerField(
        choices=MODULE_CHOICES, 
        default=0, 
        help_text="Module number for notes/textbooks"
    )
    exam_type = models.CharField(
        max_length=20, 
        choices=EXAM_TYPE_CHOICES, 
        blank=True,
        help_text="Exam type for PYQ"
    )
    exam_year = models.PositiveIntegerField(
        blank=True, 
        null=True,
        help_text="Year of exam for PYQ"
    )
    
    # Additional metadata
    author = models.CharField(max_length=200, blank=True, help_text="Author for textbooks")
    publisher = models.CharField(max_length=200, blank=True, help_text="Publisher for textbooks")
    edition = models.CharField(max_length=50, blank=True, help_text="Edition for textbooks")
    isbn = models.CharField(max_length=20, blank=True, help_text="ISBN for textbooks")
    
    # Upload and approval system
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_resources')
    is_approved = models.BooleanField(default=False)
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL, 
        null=True, 
        blank=True, 
        related_name='approved_resources'
    )
    approved_at = models.DateTimeField(null=True, blank=True)
    
    # Statistics
    download_count = models.PositiveIntegerField(default=0)
    view_count = models.PositiveIntegerField(default=0)
    
    # Status
    is_featured = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-is_featured', '-created_at']
        indexes = [
            models.Index(fields=['category', 'subject', 'is_approved']),
            models.Index(fields=['uploaded_by']),
            models.Index(fields=['category', 'module_number']),
            models.Index(fields=['exam_type', 'exam_year']),
        ]
    
    def __str__(self):
        status = "✓" if self.is_approved else "⏳"
        category_name = self.category.get_category_type_display()
        
        if self.category.category_type == 'notes' and self.module_number > 0:
            return f"{status} {self.title} - {self.subject.name} (Module {self.module_number})"
        elif self.category.category_type == 'pyq' and self.exam_year:
            return f"{status} {self.title} - {self.subject.name} ({self.exam_year} {self.get_exam_type_display()})"
        else:
            return f"{status} {self.title} - {self.subject.name}"
    
    def save(self, *args, **kwargs):
        # Set file size if file exists
        if self.file:
            self.file_size = self.file.size
        super().save(*args, **kwargs)
    
    @property
    def file_size_mb(self):
        if self.file_size:
            return round(self.file_size / (1024 * 1024), 2)
        return 0
    
    def can_be_approved_by(self, user):
        """Check if user can approve this resource"""
        # Only staff with can_verify_notes permission can approve
        if hasattr(user, 'can_verify_notes') and user.can_verify_notes:
            return True
        
        return False


class ResourceDownload(models.Model):
    """Track resource downloads"""
    
    resource = models.ForeignKey(AcademicResource, on_delete=models.CASCADE, related_name='downloads')
    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name='downloads')
    downloaded_at = models.DateTimeField(auto_now_add=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    
    class Meta:
        unique_together = ['resource', 'user', 'downloaded_at']
        ordering = ['-downloaded_at']
        
    def __str__(self):
        return f"{self.user.username} downloaded {self.resource.title}"
