from django.contrib.auth.models import AbstractUser
from django.db import models
from django.core.validators import RegexValidator


def team_member_upload_path(instance, filename):
    """Generate upload path for team member images"""
    import os
    name, ext = os.path.splitext(filename)
    safe_name = "".join(c for c in instance.name if c.isalnum() or c in (' ', '-', '_')).rstrip()[:20]
    return f'team_members/{instance.team_type}/{safe_name.replace(" ", "_")}{ext}'


class User(AbstractUser):
    """Custom User model with groups-based permissions"""
    
    email = models.EmailField(unique=True)
    mobile_number = models.CharField(
        max_length=15, 
        blank=True, 
        null=True,
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Enter a valid mobile number")]
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    USERNAME_FIELD = 'username'
    REQUIRED_FIELDS = ['email']
    
    def __str__(self):
        return f"{self.username} ({self.email})"
    
    @property
    def is_staff_member(self):
        """Check if user is staff based on groups"""
        return self.is_superuser or self.groups.exists()


class TeamMember(models.Model):
    """Team members for EESA and Tech teams"""
    
    TEAM_TYPE_CHOICES = [
        ('eesa', 'EESA Team'),
        ('tech', 'Tech Team'),
    ]
    
    # Basic Information
    name = models.CharField(max_length=100)
    position = models.CharField(max_length=100, help_text="Role/Position in the team")
    bio = models.TextField(help_text="Brief description about the member")
    image = models.ImageField(upload_to=team_member_upload_path, blank=True, null=True)
    
    # Contact Information
    email = models.EmailField(blank=True, null=True)
    linkedin_url = models.URLField(blank=True, null=True)
    github_url = models.URLField(blank=True, null=True)
    
    # Team Classification
    team_type = models.CharField(max_length=10, choices=TEAM_TYPE_CHOICES)
    is_active = models.BooleanField(default=True, help_text="Is this member currently active?")
    order = models.PositiveIntegerField(default=0, help_text="Display order (lower numbers appear first)")
    
    # Metadata
    created_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['team_type', 'order', 'name']
        verbose_name = "Team Member"
        verbose_name_plural = "Team Members"
    
    def __str__(self):
        return f"{self.name} - {self.position} ({self.get_team_type_display()})" 