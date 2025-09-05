from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()

class JobOpportunity(models.Model):
    JOB_TYPES = [
        ('full_time', 'Full Time'),
        ('part_time', 'Part Time'),
        ('internship', 'Internship'),
        ('contract', 'Contract'),
    ]
    
    EXPERIENCE_LEVELS = [
        ('entry', 'Entry Level'),
        ('mid', 'Mid Level'),
        ('senior', 'Senior Level'),
    ]
    
    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    job_type = models.CharField(max_length=20, choices=JOB_TYPES, default='full_time')
    experience_level = models.CharField(max_length=20, choices=EXPERIENCE_LEVELS, default='entry')
    description = models.TextField()
    requirements = models.TextField(help_text="List requirements separated by newlines")
    skills = models.TextField(help_text="List skills separated by commas")
    salary_range = models.CharField(max_length=100, blank=True, null=True)
    application_url = models.URLField()
    application_deadline = models.DateTimeField(blank=True, null=True)
    
    # Meta fields
    posted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posted_jobs')
    posted_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-posted_at']
        indexes = [
            models.Index(fields=['job_type', 'experience_level']),
            models.Index(fields=['posted_at']),
            models.Index(fields=['is_active']),
            models.Index(fields=['company']),
            models.Index(fields=['application_deadline']),
        ]
        
    def __str__(self):
        return f"{self.title} at {self.company}"
    
    @property
    def requirements_list(self):
        return [req.strip() for req in self.requirements.split('\n') if req.strip()]
    
    @property
    def skills_list(self):
        return [skill.strip() for skill in self.skills.split(',') if skill.strip()]


class InternshipOpportunity(models.Model):
    DURATION_CHOICES = [
        ('less_than_month', 'Less than a month'),
        ('1_month', '1 Month'),
        ('2_months', '2 Months'), 
        ('3_months', '3 Months'),
        ('6_months', '6 Months'),
        ('1_year', '1 Year'),
        ('other', 'Other'),
    ]
    
    INTERNSHIP_TYPES = [
        ('paid', 'Paid'),
        ('unpaid', 'Unpaid'),
        ('stipend', 'Stipend Based'),
    ]
    
    title = models.CharField(max_length=200)
    company = models.CharField(max_length=200)
    location = models.CharField(max_length=200)
    duration = models.CharField(max_length=20, choices=DURATION_CHOICES)
    internship_type = models.CharField(max_length=20, choices=INTERNSHIP_TYPES, default='stipend')
    description = models.TextField()
    requirements = models.TextField(help_text="List requirements separated by newlines")
    skills = models.TextField(help_text="List skills separated by commas")
    stipend_amount = models.CharField(max_length=100, blank=True, null=True)
    application_url = models.URLField()
    application_deadline = models.DateTimeField(blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    
    # Additional fields for internships
    is_remote = models.BooleanField(default=False)
    certificate_provided = models.BooleanField(default=True)
    letter_of_recommendation = models.BooleanField(default=False)
    
    # Meta fields
    posted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posted_internships')
    posted_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-posted_at']
        indexes = [
            models.Index(fields=['internship_type', 'duration']),
            models.Index(fields=['posted_at']),
            models.Index(fields=['is_active']),
            models.Index(fields=['company']),
            models.Index(fields=['application_deadline']),
            models.Index(fields=['is_remote']),
        ]
        
    def __str__(self):
        return f"{self.title} at {self.company} ({self.duration})"
    
    @property
    def requirements_list(self):
        return [req.strip() for req in self.requirements.split('\n') if req.strip()]
    
    @property
    def skills_list(self):
        return [skill.strip() for skill in self.skills.split(',') if skill.strip()]


class CertificateOpportunity(models.Model):
    CERTIFICATE_TYPES = [
        ('course', 'Online Course'),
        ('certification', 'Professional Certification'),
        ('workshop', 'Workshop Certificate'),
        ('competition', 'Competition Certificate'),
        ('training', 'Training Program'),
    ]
    
    PROVIDERS = [
        ('coursera', 'Coursera'),
        ('edx', 'edX'),
        ('udemy', 'Udemy'),
        ('linkedin', 'LinkedIn Learning'),
        ('ieee', 'IEEE'),
        ('cisco', 'Cisco'),
        ('microsoft', 'Microsoft'),
        ('google', 'Google'),
        ('amazon', 'Amazon Web Services'),
        ('other', 'Other'),
    ]
    
    title = models.CharField(max_length=200)
    provider = models.CharField(max_length=50, choices=PROVIDERS)
    certificate_type = models.CharField(max_length=20, choices=CERTIFICATE_TYPES, default='course')
    description = models.TextField()
    duration = models.CharField(max_length=100, help_text="e.g., 4 weeks, 6 months")
    prerequisites = models.TextField(blank=True, null=True, help_text="List prerequisites separated by newlines")
    skills_covered = models.TextField(help_text="List skills covered separated by commas")
    
    # Pricing and access
    is_free = models.BooleanField(default=False)
    price = models.CharField(max_length=100, blank=True, null=True)
    financial_aid_available = models.BooleanField(default=False)
    percentage_offer = models.DecimalField(
        max_digits=5, decimal_places=2, blank=True, null=True,
        help_text="Discount percentage if any (e.g., 20.00 for 20% off)"
    )
    validity_till = models.DateTimeField(
        blank=True, null=True,
        help_text="Validity date for the offer/course"
    )
    
    # Links and deadlines
    course_url = models.URLField()
    registration_deadline = models.DateTimeField(blank=True, null=True)
    start_date = models.DateField(blank=True, null=True)
    
    # Certificate benefits
    industry_recognized = models.BooleanField(default=False)
    university_credit = models.BooleanField(
        default=False, 
        help_text="Check this if the certification provides university credit"
    )
    credit_hours = models.DecimalField(
        max_digits=4, decimal_places=1, blank=True, null=True,
        help_text="Enter credit hours ONLY if university credit is available. Leave blank if university credit is not checked."
    )
    
    # Meta fields
    posted_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='posted_certificates')
    posted_at = models.DateTimeField(auto_now_add=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-posted_at']
        indexes = [
            models.Index(fields=['certificate_type', 'provider']),
            models.Index(fields=['posted_at']),
            models.Index(fields=['is_active']),
            models.Index(fields=['is_free']),
            models.Index(fields=['university_credit']),
            models.Index(fields=['validity_till']),
        ]
        
    def clean(self):
        from django.core.exceptions import ValidationError
        
        # Validate credit system with clear error messages
        if not self.university_credit and self.credit_hours:
            raise ValidationError({
                'credit_hours': 'You cannot enter credit hours when "University Credit" is not checked. Either check "University Credit" or clear the credit hours field.'
            })
        
        if self.university_credit and not self.credit_hours:
            raise ValidationError({
                'credit_hours': 'You must specify credit hours when "University Credit" is checked. Please enter the number of credit hours (e.g., 3.0).'
            })
        
    def save(self, *args, **kwargs):
        # Clear credit_hours if university_credit is False
        if not self.university_credit:
            self.credit_hours = None
        self.clean()
        super().save(*args, **kwargs)
        
    def __str__(self):
        return f"{self.title} - {self.provider}"
    
    @property
    def prerequisites_list(self):
        if not self.prerequisites:
            return []
        return [req.strip() for req in self.prerequisites.split('\n') if req.strip()]
    
    @property
    def skills_list(self):
        return [skill.strip() for skill in self.skills_covered.split(',') if skill.strip()]
