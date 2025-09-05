from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import EmailValidator
from django.utils import timezone

User = get_user_model()


class AlumniBatch(models.Model):
    """
    Model to represent alumni batches (e.g., 2022-2026, 2023-2027)
    """
    batch_year_range = models.CharField(
        max_length=20, 
        unique=True,
        help_text="Batch year range (e.g., '2022-2026', '2023-2027')"
    )
    batch_name = models.CharField(max_length=100, help_text="e.g., 'Batch 2022-2026', 'Class of 2026'")
    batch_description = models.TextField(blank=True, null=True, help_text="Description of the batch")
    
    # Batch Statistics (computed from Alumni model)
    total_alumni = models.IntegerField(default=0, help_text="Total number of alumni in this batch")
    verified_alumni = models.IntegerField(default=0, help_text="Number of verified alumni in this batch")
    
    # Batch Media
    batch_group_photo = models.ImageField(
        upload_to='alumni/batch_photos/',
        blank=True, null=True,
        help_text="Official graduation/group photo of the batch"
    )
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-batch_year_range']
        verbose_name = 'Alumni Batch'
        verbose_name_plural = 'Alumni Batches'
    
    def __str__(self):
        return self.batch_name
    
    @property
    def graduation_year(self):
        """Extract graduation year from batch range (e.g., 2026 from '2022-2026')"""
        try:
            return int(self.batch_year_range.split('-')[1])
        except (ValueError, IndexError):
            return None
    
    @property
    def joining_year(self):
        """Extract joining year from batch range (e.g., 2022 from '2022-2026')"""
        try:
            return int(self.batch_year_range.split('-')[0])
        except (ValueError, IndexError):
            return None
    
    def update_statistics(self):
        """Update batch statistics from Alumni model"""
        alumni_in_batch = Alumni.objects.filter(batch=self, is_active=True)
        self.total_alumni = alumni_in_batch.count()
        self.verified_alumni = alumni_in_batch.filter(is_verified=True).count()
        self.save(update_fields=['total_alumni', 'verified_alumni', 'updated_at'])
    
    @property
    def employment_stats(self):
        """Get employment statistics for this batch"""
        alumni_in_batch = Alumni.objects.filter(batch=self, is_active=True)
        total = alumni_in_batch.count()
        
        if total == 0:
            return {}
        
        employed = alumni_in_batch.filter(employment_status='employed').count()
        self_employed = alumni_in_batch.filter(employment_status='self_employed').count()
        entrepreneur = alumni_in_batch.filter(employment_status='entrepreneur').count()
        higher_studies = alumni_in_batch.filter(employment_status='higher_studies').count()
        unemployed = alumni_in_batch.filter(employment_status='unemployed').count()
        
        return {
            'total': total,
            'employed': employed,
            'self_employed': self_employed,
            'entrepreneur': entrepreneur,
            'higher_studies': higher_studies,
            'unemployed': unemployed,
            'employment_rate': round((employed + self_employed + entrepreneur) / total * 100, 2)
        }


class Alumni(models.Model):
    """Simplified Alumni model focusing on batch-based organization"""
    
    # Auto-incrementing ID starting from 100
    id = models.AutoField(primary_key=True)
    
    # Personal Information
    full_name = models.CharField(max_length=150, help_text="Full name of the alumni")
    email = models.EmailField(validators=[EmailValidator()], unique=True)
    phone_number = models.CharField(max_length=15, blank=True, null=True)
    
    # Batch Information (replaces individual year fields)
    batch = models.ForeignKey(
        AlumniBatch, 
        on_delete=models.CASCADE, 
        related_name='alumni_members',
        null=True, blank=True,  # Temporarily nullable for migration
        help_text="Select the batch this alumni belongs to"
    )
    
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
        ordering = ['id']  # Order by auto-incrementing ID
        indexes = [
            models.Index(fields=['batch']),
            models.Index(fields=['employment_status']),
            models.Index(fields=['current_company']),
            models.Index(fields=['email']),
        ]
    
    def __str__(self):
        return f"{self.full_name} ({self.batch.batch_name})"
    
    @property
    def years_since_graduation(self):
        """Calculate years since graduation based on batch"""
        if self.batch and self.batch.graduation_year:
            current_year = timezone.now().year
            return current_year - self.batch.graduation_year
        return None
    
    @property
    def batch_name(self):
        """Return batch identifier"""
        return self.batch.batch_name if self.batch else "No Batch"
    
    def save(self, *args, **kwargs):
        # For PostgreSQL, we'll set the starting sequence value differently
        if not self.pk:
            # Get the highest existing ID and start from 100 if none exist
            last_alumni = Alumni.objects.order_by('-id').first()
            if not last_alumni:
                # First record should start from 100
                from django.db import connection
                with connection.cursor() as cursor:
                    # PostgreSQL syntax for setting sequence start value
                    cursor.execute("SELECT setval('alumni_alumni_id_seq', 99, false)")
        
        super().save(*args, **kwargs)
