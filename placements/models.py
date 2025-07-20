from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import URLValidator, RegexValidator

User = get_user_model()


def company_logo_upload_path(instance, filename):
    """Generate upload path for company logos"""
    import os
    name, ext = os.path.splitext(filename)
    safe_name = "".join(c for c in instance.name if c.isalnum() or c in (' ', '-', '_')).rstrip()[:25]
    return f'companies/logos/{safe_name.replace(" ", "_")}{ext}'


def resume_upload_path(instance, filename):
    """Generate upload path for placement resumes"""
    import os
    name, ext = os.path.splitext(filename)
    safe_name = "".join(c for c in instance.student_name if c.isalnum() or c in (' ', '-', '_')).rstrip()[:20]
    safe_company = "".join(c for c in instance.placement_drive.company.name if c.isalnum() or c in (' ', '-', '_')).rstrip()[:20]
    return f'placements/resumes/{safe_company.replace(" ", "_")}/{safe_name.replace(" ", "_")}{ext}'


def placement_brochure_upload_path(instance, filename):
    """Generate upload path for department placement brochures"""
    import os
    name, ext = os.path.splitext(filename)
    return f'placement_brochures/eee_dept/{instance.academic_year.replace("-", "_")}/{filename}'


class Company(models.Model):
    """Company model for placement opportunities"""
    name = models.CharField(max_length=200, unique=True)
    description = models.TextField(blank=True)
    website = models.URLField(blank=True, validators=[URLValidator()])
    logo = models.ImageField(upload_to=company_logo_upload_path, blank=True, null=True)
    
    # Company details
    industry = models.CharField(max_length=100, blank=True)
    location = models.CharField(max_length=200, blank=True)
    company_size = models.CharField(max_length=50, blank=True, choices=[
        ('startup', 'Startup (1-50)'),
        ('small', 'Small (51-200)'),
        ('medium', 'Medium (201-1000)'),
        ('large', 'Large (1000+)'),
    ])
    
    # Contact information
    contact_person = models.CharField(max_length=100, blank=True)
    contact_email = models.EmailField(blank=True)
    contact_phone = models.CharField(
        max_length=15, 
        blank=True,
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$')]
    )
    
    # Status
    is_active = models.BooleanField(default=True)
    is_verified = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-created_at']
        
    def __str__(self):
        return self.name


class PlacementDrive(models.Model):
    """Placement drive/recruitment event model"""
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='placement_drives')
    title = models.CharField(max_length=200)
    description = models.TextField()
    
    # Drive details
    job_type = models.CharField(max_length=50, choices=[
        ('full_time', 'Full Time'),
        ('internship', 'Internship'),
        ('part_time', 'Part Time'),
        ('contract', 'Contract'),
    ])
    
    # Requirements
    min_cgpa = models.DecimalField(max_digits=3, decimal_places=2, default=0.0)
    min_percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0.0)
    eligible_batches = models.JSONField(default=list, help_text="List of eligible graduation years")
    
    # Package details
    package_lpa = models.DecimalField(max_digits=10, decimal_places=2, null=True, blank=True)
    package_details = models.TextField(blank=True)
    
    # Important dates
    registration_start = models.DateTimeField()
    registration_end = models.DateTimeField()
    drive_date = models.DateTimeField()
    result_date = models.DateTimeField(null=True, blank=True)
    
    # Additional details
    location = models.CharField(max_length=200, blank=True)
    drive_mode = models.CharField(max_length=20, choices=[
        ('online', 'Online'),
        ('offline', 'Offline'),
        ('hybrid', 'Hybrid'),
    ], default='offline')
    
    # Application
    application_link = models.URLField(default="https://example.com/apply", help_text="Link for students to apply for this placement drive")
    
    # Requirements documents
    required_documents = models.JSONField(default=list, help_text="List of required documents")
    additional_info = models.TextField(blank=True)
    
    # Status
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-drive_date']
        
    def __str__(self):
        return f"{self.company.name} - {self.title}"
    
    @property
    def is_registration_open(self):
        from django.utils import timezone
        now = timezone.now()
        # Handle None values during creation
        if not self.registration_start or not self.registration_end:
            return False
        return self.registration_start <= now <= self.registration_end
    
    @property
    def is_upcoming(self):
        from django.utils import timezone
        # Handle None values during creation
        if not self.drive_date:
            return False
        return self.drive_date > timezone.now()


class PlacementApplication(models.Model):
    """Student application for placement drives"""
    drive = models.ForeignKey(PlacementDrive, on_delete=models.CASCADE, related_name='applications')
    student = models.ForeignKey(User, on_delete=models.CASCADE, related_name='placement_applications')
    
    # Application status
    status = models.CharField(max_length=20, choices=[
        ('applied', 'Applied'),
        ('shortlisted', 'Shortlisted'),
        ('selected', 'Selected'),
        ('rejected', 'Rejected'),
        ('withdrawn', 'Withdrawn'),
    ], default='applied')
    
    # Application details
    cover_letter = models.TextField(blank=True)
    resume = models.FileField(
        upload_to=resume_upload_path, 
        blank=True, 
        null=True,
        help_text="Upload resume (PDF only). Maximum file size: 15MB."
    )
    additional_documents = models.JSONField(default=dict, help_text="Additional documents as JSON")
    
    # Interview details
    interview_date = models.DateTimeField(null=True, blank=True)
    interview_mode = models.CharField(max_length=20, choices=[
        ('online', 'Online'),
        ('offline', 'Offline'),
    ], blank=True)
    interview_notes = models.TextField(blank=True)
    
    # Results
    result_status = models.CharField(max_length=20, choices=[
        ('pending', 'Pending'),
        ('selected', 'Selected'),
        ('not_selected', 'Not Selected'),
    ], default='pending')
    
    feedback = models.TextField(blank=True)
    
    # Metadata
    applied_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['drive', 'student']
        ordering = ['-applied_at']
        
    def __str__(self):
        return f"{self.student.get_full_name()} - {self.drive.title}"


def student_coordinator_image_upload_path(instance, filename):
    """Upload path for student coordinator images"""
    return f'coordinators/images/{instance.user.username}_{filename}'


class StudentCoordinator(models.Model):
    """Student coordinator model for display purposes"""
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='student_coordinator')
    designation = models.CharField(max_length=100, default="Placement Coordinator")
    
    # Personal details
    profile_picture = models.ImageField(
        upload_to=student_coordinator_image_upload_path, 
        help_text="Upload coordinator's profile picture"
    )
    mobile_number = models.CharField(max_length=15, help_text="Contact mobile number")
    email = models.EmailField(help_text="Contact email address")
    
    # Additional info
    bio = models.TextField(blank=True, help_text="Brief bio or description")
    
    # Display settings
    is_active = models.BooleanField(default=True, help_text="Show in public listings")
    display_order = models.IntegerField(default=0, help_text="Order for display (lower numbers appear first)")
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['display_order', 'user__first_name']
        verbose_name = "Student Coordinator"
        verbose_name_plural = "Student Coordinators"
    
    def __str__(self):
        return f"{self.user.get_full_name()} - {self.designation}"


class PlacementStatistics(models.Model):
    """Placement statistics for tracking and reporting"""
    academic_year = models.CharField(max_length=9, help_text="e.g., 2024-2025")
    batch_year = models.IntegerField(help_text="Graduation year")
    branch = models.CharField(max_length=100)
    
    # Statistics
    total_students = models.IntegerField(default=0)
    total_placed = models.IntegerField(default=0)
    highest_package = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    average_package = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    median_package = models.DecimalField(max_digits=10, decimal_places=2, default=0.0)
    
    # Company counts
    total_companies_visited = models.IntegerField(default=0)
    total_offers = models.IntegerField(default=0)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        unique_together = ['academic_year', 'batch_year', 'branch']
        ordering = ['-batch_year', 'branch']
        
    def __str__(self):
        return f"{self.branch} - {self.batch_year} ({self.academic_year})"
    
    @property
    def placement_percentage(self):
        if self.total_students > 0:
            return (self.total_placed / self.total_students) * 100
        return 0.0


class PlacedStudent(models.Model):
    """Model to track students who got placed"""
    # Student information
    student_name = models.CharField(max_length=200)
    student_email = models.EmailField()
    roll_number = models.CharField(max_length=50)
    batch_year = models.IntegerField(help_text="Graduation year")
    cgpa = models.DecimalField(max_digits=4, decimal_places=2)
    
    # Placement details
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='placed_students')
    placement_drive = models.ForeignKey(PlacementDrive, on_delete=models.SET_NULL, null=True, blank=True)
    job_title = models.CharField(max_length=200)
    package_lpa = models.DecimalField(max_digits=10, decimal_places=2)
    package_details = models.TextField(blank=True, help_text="Additional package details")
    
    # Work details
    work_location = models.CharField(max_length=200, blank=True)
    job_type = models.CharField(max_length=50, choices=[
        ('full_time', 'Full Time'),
        ('internship', 'Internship'),
        ('contract', 'Contract'),
    ], default='full_time')
    
    # Dates
    offer_date = models.DateField()
    joining_date = models.DateField(null=True, blank=True)
    
    # Additional information
    offer_letter = models.FileField(
        upload_to='placement_offers/', 
        blank=True, 
        null=True,
        help_text="Upload offer letter (PDF only). Maximum file size: 15MB."
    )
    student_photo = models.ImageField(upload_to='placed_students/', blank=True, null=True)
    testimonial = models.TextField(blank=True, help_text="Student testimonial about placement")
    
    # Status
    is_verified = models.BooleanField(default=False, help_text="Verified by placement coordinator")
    is_active = models.BooleanField(default=True)
    
    # Metadata
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    
    class Meta:
        ordering = ['-offer_date', '-package_lpa']
        unique_together = ['student_email', 'company', 'offer_date']
        
    def __str__(self):
        return f"{self.student_name} - {self.company.name} ({self.package_lpa} LPA)"


class PlacementBrochure(models.Model):
    """Department placement brochure/information documents"""
    title = models.CharField(max_length=200, help_text="Brochure title or description")
    file = models.FileField(
        upload_to=placement_brochure_upload_path, 
        help_text="Upload placement brochure (PDF only). Maximum file size: 15MB."
    )
    description = models.TextField(blank=True, help_text="Additional information about the brochure")
    
    # Brochure details
    academic_year = models.CharField(max_length=9, help_text="e.g., 2024-2025")
    is_current = models.BooleanField(default=True, help_text="Whether this is the current/active brochure")
    
    # Metadata
    uploaded_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-created_at']
        unique_together = ['academic_year']
        
    def __str__(self):
        return f"EEE Department - {self.title} ({self.academic_year})"
