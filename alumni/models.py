from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import MinValueValidator, MaxValueValidator, EmailValidator
from django.utils import timezone
import uuid

User = get_user_model()


class Alumni(models.Model):
    """Alumni model for managing former students"""
    
    # Unique identifier
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    
    # Personal Information
    full_name = models.CharField(max_length=150, help_text="Full name of the alumni")
    email = models.EmailField(validators=[EmailValidator()], unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    alternative_phone = models.CharField(max_length=15, blank=True, null=True)
    
    # Academic Information
    student_id = models.CharField(max_length=20, blank=True, null=True, help_text="Original student ID")
    scheme = models.PositiveIntegerField(blank=True, null=True, help_text="Academic scheme year (e.g., 2019, 2021)")
    year_of_joining = models.PositiveIntegerField(help_text="Year joined the institution")
    year_of_passout = models.PositiveIntegerField(help_text="Year of graduation")
    department = models.CharField(max_length=100, default="Electrical and Electronics Engineering", editable=False)
    specialization = models.CharField(max_length=100, blank=True, null=True)
    cgpa = models.DecimalField(max_digits=4, decimal_places=2, blank=True, null=True,
                              validators=[MinValueValidator(0.0), MaxValueValidator(10.0)])
    
    # Current Status
    job_title = models.CharField(max_length=150, blank=True, null=True, help_text="Current job title or designation")
    current_company = models.CharField(max_length=200, blank=True, null=True)
    current_location = models.CharField(max_length=100, blank=True, null=True)
    linkedin_profile = models.URLField(blank=True, null=True)
    
    # Employment Information
    EMPLOYMENT_STATUS_CHOICES = [
        ('employed', 'Employed'),
        ('self_employed', 'Self Employed'),
        ('unemployed', 'Unemployed'),
        ('higher_studies', 'Higher Studies'),
        ('entrepreneur', 'Entrepreneur'),
        ('other', 'Other'),
    ]
    employment_status = models.CharField(max_length=20, choices=EMPLOYMENT_STATUS_CHOICES, default='employed')
    
    # Additional Information
    achievements = models.TextField(blank=True, null=True, help_text="Notable achievements or awards")
    feedback = models.TextField(blank=True, null=True, help_text="Feedback about the institution")
    
    # Contact Preferences
    willing_to_mentor = models.BooleanField(default=False)
    allow_contact_from_juniors = models.BooleanField(default=True)
    newsletter_subscription = models.BooleanField(default=True)
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True,
                                 related_name='created_alumni')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    is_verified = models.BooleanField(default=False, help_text="Email verification status")
    is_active = models.BooleanField(default=True, help_text="Active status in alumni network")
    
    class Meta:
        verbose_name = "Alumni"
        verbose_name_plural = "Alumni"
        ordering = ['-year_of_passout', 'full_name']
        indexes = [
            models.Index(fields=['year_of_passout', 'department']),
            models.Index(fields=['scheme', 'year_of_joining']),
            models.Index(fields=['employment_status']),
            models.Index(fields=['current_company']),
            models.Index(fields=['email']),
        ]
    
    def __str__(self):
        return f"{self.full_name} ({self.year_of_passout} - {self.department})"
    
    @property
    def years_since_graduation(self):
        """Calculate years since graduation"""
        if self.year_of_passout is None:
            return None
        current_year = timezone.now().year
        return current_year - self.year_of_passout
    
    @property
    def batch_name(self):
        """Return batch identifier"""
        if self.year_of_passout is None:
            return "Batch TBD"
        return f"Batch {self.year_of_passout}"
