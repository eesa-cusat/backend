from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator
from django.core.exceptions import ValidationError
from django.conf import settings
from django.core.files.storage import FileSystemStorage

# Import Cloudinary storage only in production
if not settings.DEBUG:
    from cloudinary_storage.storage import MediaCloudinaryStorage
    from .storage import PDFCloudinaryStorage

def get_storage():
    """Get the appropriate storage backend based on environment"""
    if settings.DEBUG:
        return FileSystemStorage()
    else:
        try:
            from .storage import PDFCloudinaryStorage, CLOUDINARY_AVAILABLE
            if CLOUDINARY_AVAILABLE:
                return PDFCloudinaryStorage()
            else:
                return FileSystemStorage()
        except ImportError:
            return FileSystemStorage()

User = get_user_model()

# Department choices for Subject
DEPARTMENT_CHOICES = [
    ("EEE", "Electrical & Electronics Engineering"),
    ("ECE", "Electronics & Communication Engineering"),
    ("IT", "Information Technology Engineering"),
    ("CS", "Computer Science & Engineering"),
    ("ME", "Mechanical Engineering"),
    ("SFE", "Safety & Fire Engineering"),
    ("CE", "Civil Engineering"),
]

SEMESTER_CHOICES = [(i, f"Semester {i}") for i in range(1, 9)]

# Academic categories
ACADEMIC_CATEGORIES = [
    ('notes', 'Notes'),
    ('textbook', 'Textbooks'),
    ('pyq', 'Previous Year Questions'),
    ('regulations', 'Regulations'),
    ('syllabus', 'Syllabus'),
]

class Scheme(models.Model):
    """Academic scheme model (2018, 2022, etc.)"""
    year = models.PositiveIntegerField(unique=True)
    name = models.CharField(max_length=100, help_text="e.g., 'Scheme 2018', 'CBCS 2022'")
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ['-year']

    def __str__(self):
        return f"{self.name} ({self.year})"

class Subject(models.Model):
    """Subject model with department and semester"""
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20)
    scheme = models.ForeignKey(Scheme, on_delete=models.CASCADE, related_name='subjects')
    semester = models.IntegerField(choices=SEMESTER_CHOICES)
    department = models.CharField(max_length=10, choices=DEPARTMENT_CHOICES, default="EEE")
    credits = models.PositiveIntegerField(default=3)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['code', 'scheme', 'semester']
        ordering = ['scheme__year', 'semester', 'name']
        indexes = [
            models.Index(fields=['scheme', 'semester']),
            models.Index(fields=['code']),
            models.Index(fields=['department']),
        ]

    def __str__(self):
        return f"{self.code} - {self.name} ({self.scheme.name} Sem{self.semester})"

def academic_resource_upload_path(instance, filename):
    """Generate upload path for academic resources with proper hierarchy"""
    # Clean the filename to remove any problematic characters and ensure it's URL-safe
    import re
    clean_filename = re.sub(r'[^a-zA-Z0-9._-]', '_', filename)
    
    # Remove .pdf extension if it exists to avoid double extensions
    if clean_filename.lower().endswith('.pdf'):
        clean_filename = clean_filename[:-4]  # Remove .pdf
    
    # Main category: academics
    # Subcategory: category (notes, textbook, pyq, etc.)
    # Year: scheme year
    # Semester: semester number
    # Department: department code
    # Subject: subject code
    base_path = f"academics/{instance.category}/{instance.subject.scheme.year}/semester_{instance.subject.semester}/{instance.subject.department}/{instance.subject.code}"
    
    # Add module number for notes category
    if instance.category == 'notes' and instance.module_number > 0:
        base_path += f"/module_{instance.module_number}"
    
    # Return the path without .pdf extension (storage will add it)
    return f"{base_path}/{clean_filename}"

class AcademicResource(models.Model):
    """Academic resources like notes, textbooks, and previous year questions"""
    
    MODULE_CHOICES = [
        (1, 'Module 1'),
        (2, 'Module 2'),
        (3, 'Module 3'),
        (4, 'Module 4'),
        (5, 'Module 5'),
        (0, 'General/Complete'),
    ]

    # Basic Information
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True)
    category = models.CharField(max_length=20, choices=ACADEMIC_CATEGORIES)
    subject = models.ForeignKey(Subject, on_delete=models.CASCADE, related_name='resources')
    
    # File Information
    file = models.FileField(
        upload_to=academic_resource_upload_path,
        validators=[FileExtensionValidator(allowed_extensions=['pdf'])],
        help_text="Upload only PDF files. Maximum file size: 15MB.",
        max_length=255,  # Increased for Cloudinary URLs
        storage=get_storage()
    )
    file_size = models.BigIntegerField(blank=True, null=True)

    # Resource Details
    module_number = models.PositiveIntegerField(
        choices=MODULE_CHOICES, 
        default=0,
        help_text="Module number (only for notes)"
    )

    # Upload and Status
    uploaded_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='uploaded_resources')
    approved_by = models.ForeignKey(
        User, 
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name='approved_resources'
    )
    is_approved = models.BooleanField(default=False)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    # Statistics
    download_count = models.PositiveIntegerField(default=0)
    like_count = models.PositiveIntegerField(default=0)

    class Meta:
        ordering = ['-created_at']
        indexes = [
            models.Index(fields=['category', 'subject']),
            models.Index(fields=['uploaded_by']),
            models.Index(fields=['is_approved']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.title} - {self.subject.name} ({self.get_category_display()})"

    def clean(self):
        if self.file:
            # Validate file type
            if not self.file.name.lower().endswith('.pdf'):
                raise ValidationError('Only PDF files are allowed.')
            
            # Validate file size (15MB limit)
            if self.file.size > 15 * 1024 * 1024:
                raise ValidationError('File size must be less than 15MB.')
        
        super().clean()

    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
        super().save(*args, **kwargs)

    @property
    def file_size_mb(self):
        return round(self.file_size / (1024 * 1024), 2) if self.file_size else 0

    @property
    def file_url(self):
        """Get the file URL based on environment"""
        if self.file:
            # In development, use local file URL
            if settings.DEBUG:
                return self.file.url if hasattr(self.file, 'url') else str(self.file)
            
            # In production, handle Cloudinary URLs
            file_str = str(self.file)
            
            # If it's already a full Cloudinary URL, use it directly
            if file_str.startswith('http'):
                # Fix the missing slash issue
                if 'https:/res.cloudinary.com' in file_str:
                    fixed_url = file_str.replace('https:/res.cloudinary.com', 'https://res.cloudinary.com')
                    return fixed_url
                return file_str
            
            # For new uploads, use the file.url which should be the correct Cloudinary URL
            if hasattr(self.file, 'url') and self.file.url:
                url = self.file.url
                # If the file field is already a full URL, don't use file.url as it creates malformed URLs
                if file_str.startswith('http'):
                    # Just use the file field string directly
                    return file_str
                
                # Ensure the URL is properly formatted for PDF preview
                if url and 'res.cloudinary.com' in url:
                    # Make sure we're using the raw resource URL
                    if '/image/upload/' in url:
                        url = url.replace('/image/upload/', '/raw/upload/')
                    return url
                return url
            
            # Fallback to the file field string
            return file_str
        else:
            return None

    def get_download_url(self):
        """Get a download URL for the file with proper headers"""
        if self.file:
            base_url = self.file_url
            if base_url:
                # Add download parameter to force download
                if '?' in base_url:
                    return f"{base_url}&fl_attachment"
                else:
                    return f"{base_url}?fl_attachment"
        return None

class ResourceLike(models.Model):
    """Track resource likes with IP addresses"""
    resource = models.ForeignKey(AcademicResource, on_delete=models.CASCADE, related_name='likes')
    ip_address = models.GenericIPAddressField()
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ['resource', 'ip_address']
        indexes = [
            models.Index(fields=['resource', 'ip_address']),
            models.Index(fields=['created_at']),
        ]

    def __str__(self):
        return f"{self.ip_address} liked {self.resource.title}"
