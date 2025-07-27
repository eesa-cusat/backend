from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import FileExtensionValidator

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
    """Generate upload path for academic resources"""
    # Clean the filename to remove any problematic characters
    clean_filename = "".join(c for c in filename if c.isalnum() or c in ('-', '_', '.'))
    return f"academics/{instance.category}/{instance.subject.scheme.year}/{instance.subject.semester}/{instance.subject.code}/{clean_filename}"

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
        max_length=255  # Increased for Cloudinary URLs
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
            # Check file extension
            if not self.file.name.lower().endswith('.pdf'):
                from django.core.exceptions import ValidationError
                raise ValidationError({'file': 'Only PDF files are allowed. Please upload a PDF document.'})
            
            # Check file size (15MB limit)
            if self.file.size > 15 * 1024 * 1024:
                from django.core.exceptions import ValidationError
                raise ValidationError({'file': 'File size must be less than 15MB. Please compress the file or use a smaller document.'})

    def save(self, *args, **kwargs):
        if self.file:
            self.file_size = self.file.size
        super().save(*args, **kwargs)

    @property
    def file_size_mb(self):
        return round(self.file_size / (1024 * 1024), 2) if self.file_size else 0

    @property
    def file_url(self):
        """Get the complete URL for the file"""
        if self.file:
            return self.file.url
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
