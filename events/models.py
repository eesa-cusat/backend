from django.db import models
from django.contrib.auth import get_user_model
from django.core.validators import RegexValidator
from django.utils import timezone

User = get_user_model()


def event_banner_upload_path(instance, filename):
    """Generate upload path for event banners"""
    import os
    name, ext = os.path.splitext(filename)
    safe_title = "".join(c for c in instance.title if c.isalnum() or c in (' ', '-', '_')).rstrip()[:20]
    return f'events/banners/{safe_title.replace(" ", "_")}{ext}'


def event_flyer_upload_path(instance, filename):
    """Generate upload path for event flyers"""
    import os
    name, ext = os.path.splitext(filename)
    safe_title = "".join(c for c in instance.title if c.isalnum() or c in (' ', '-', '_')).rstrip()[:20]
    return f'events/flyers/{safe_title.replace(" ", "_")}{ext}'


def payment_qr_upload_path(instance, filename):
    """Generate upload path for payment QR codes"""
    import os
    name, ext = os.path.splitext(filename)
    safe_title = "".join(c for c in instance.title if c.isalnum() or c in (' ', '-', '_')).rstrip()[:20]
    return f'events/payments/{safe_title.replace(" ", "_")}{ext}'


def speaker_profile_upload_path(instance, filename):
    """Generate upload path for speaker profile images"""
    import os
    name, ext = os.path.splitext(filename)
    safe_name = "".join(c for c in instance.name if c.isalnum() or c in (' ', '-', '_')).rstrip()[:20]
    event_title = "".join(c for c in instance.event.title if c.isalnum() or c in (' ', '-', '_')).rstrip()[:15]
    return f'events/speakers/{event_title.replace(" ", "_")}/{safe_name.replace(" ", "_")}{ext}'


class Event(models.Model):
    """Comprehensive Event management - created and managed by staff"""
    
    EVENT_TYPES = [
        ('workshop', 'Workshop'),
        ('seminar', 'Seminar'),
        ('conference', 'Conference'),
        ('hackathon', 'Hackathon'),
        ('webinar', 'Webinar'),
        ('cultural', 'Cultural Event'),
        ('technical', 'Technical Event'),
        ('sports', 'Sports Event'),
        ('competition', 'Competition'),
        ('social', 'Social Event'),
        ('other', 'Other'),
    ]
    
    STATUS_CHOICES = [
        ('draft', 'Draft'),
        ('published', 'Published'),
        ('cancelled', 'Cancelled'),
        ('completed', 'Completed'),
    ]
    
    # Basic Information
    title = models.CharField(max_length=200)
    description = models.TextField(default='')
    event_type = models.CharField(max_length=20, choices=EVENT_TYPES)
    status = models.CharField(max_length=20, choices=STATUS_CHOICES, default='draft')
    
    # Schedule
    start_date = models.DateTimeField()
    end_date = models.DateTimeField()
    registration_deadline = models.DateTimeField(blank=True, null=True)
    
    # Location
    location = models.CharField(max_length=200)
    venue = models.CharField(max_length=200, blank=True, null=True)
    address = models.TextField(blank=True, null=True)
    is_online = models.BooleanField(default=False)
    meeting_link = models.URLField(blank=True, null=True, help_text="Zoom/Teams/Meet link for online events")
    
    # Registration Settings
    registration_required = models.BooleanField(default=True)
    max_participants = models.PositiveIntegerField(blank=True, null=True, help_text="Leave blank for unlimited")
    
    # Payment Settings
    registration_fee = models.DecimalField(max_digits=10, decimal_places=2, default=0)
    payment_required = models.BooleanField(default=False)
    payment_qr_code = models.ImageField(upload_to=payment_qr_upload_path, blank=True, null=True)
    payment_upi_id = models.CharField(max_length=100, blank=True, null=True)
    payment_instructions = models.TextField(blank=True, null=True)
    
    # Contact Information
    contact_person = models.CharField(max_length=100, blank=True, null=True)
    contact_email = models.EmailField(blank=True, null=True)
    contact_phone = models.CharField(max_length=15, blank=True, null=True)
    
    # Media
    banner_image = models.ImageField(upload_to=event_banner_upload_path, blank=True, null=True)
    event_flyer = models.FileField(upload_to=event_flyer_upload_path, blank=True, null=True)
    
    # Management
    created_by = models.ForeignKey(User, on_delete=models.CASCADE, related_name='created_events')
    is_active = models.BooleanField(default=True)
    is_featured = models.BooleanField(default=False)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-start_date']
        indexes = [
            models.Index(fields=['event_type', 'status']),
            models.Index(fields=['start_date']),
            models.Index(fields=['is_featured', 'is_active']),
        ]
    
    def __str__(self):
        return f"{self.title} - {self.start_date.strftime('%Y-%m-%d')}"
    
    @property
    def is_upcoming(self):
        return self.start_date > timezone.now()
    
    @property
    def is_past(self):
        return self.end_date < timezone.now()
    
    @property
    def is_ongoing(self):
        now = timezone.now()
        return self.start_date <= now <= self.end_date
    
    @property
    def is_registration_open(self):
        if not self.registration_required or self.status != 'published':
            return False
        
        now = timezone.now()
        if self.registration_deadline and now > self.registration_deadline:
            return False
        
        if self.max_participants:
            current_count = self.registrations.count()
            return current_count < self.max_participants
        
        return self.is_upcoming
    
    @property
    def registration_count(self):
        return self.registrations.count()
    
    @property
    def spots_remaining(self):
        if not self.max_participants:
            return "Unlimited"
        return max(0, self.max_participants - self.registration_count)


class EventRegistration(models.Model):
    """Event registrations from students/external participants"""
    
    PAYMENT_STATUS = [
        ('pending', 'Payment Pending'),
        ('paid', 'Payment Completed'),
        ('exempted', 'Fee Exempted'),
        ('refunded', 'Refunded'),
    ]
    
    # Event
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='registrations')
    
    # Personal Information
    name = models.CharField(max_length=200)
    email = models.EmailField()
    mobile_number = models.CharField(
        max_length=15,
        validators=[RegexValidator(regex=r'^\+?1?\d{9,15}$', message="Enter a valid mobile number")]
    )
    
    # Academic Information (for students)
    institution = models.CharField(max_length=200, blank=True, null=True)
    department = models.CharField(max_length=100, blank=True, null=True)
    year_of_study = models.CharField(max_length=20, blank=True, null=True)
    
    # Professional Information (for external participants)
    organization = models.CharField(max_length=200, blank=True, null=True)
    designation = models.CharField(max_length=100, blank=True, null=True)
    
    # Payment Information
    payment_status = models.CharField(max_length=20, choices=PAYMENT_STATUS, default='pending')
    payment_amount = models.DecimalField(max_digits=10, decimal_places=2, blank=True, null=True)
    payment_verified_by = models.ForeignKey(User, on_delete=models.SET_NULL, null=True, blank=True, related_name='verified_payments')
    payment_date = models.DateTimeField(blank=True, null=True)
    payment_reference = models.CharField(max_length=100, blank=True, null=True)
    
    # Additional Information
    dietary_requirements = models.TextField(blank=True, null=True)
    special_needs = models.TextField(blank=True, null=True)
    
    # Attendance Tracking
    attended = models.BooleanField(default=False)
    certificate_issued = models.BooleanField(default=False)
    
    # Metadata
    registered_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        ordering = ['-registered_at']
        unique_together = ['event', 'email']
    
    def __str__(self):
        return f"{self.name} - {self.event.title}"
    
    def save(self, *args, **kwargs):
        # Set payment amount from event if not set
        if not self.payment_amount:
            self.payment_amount = self.event.registration_fee
        super().save(*args, **kwargs)


class EventSpeaker(models.Model):
    """Speakers for events"""
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='speakers')
    name = models.CharField(max_length=200)
    title = models.CharField(max_length=200, help_text="e.g., CEO, Professor, etc.")
    organization = models.CharField(max_length=200)
    bio = models.TextField(blank=True, null=True)
    profile_image = models.ImageField(upload_to=speaker_profile_upload_path, blank=True, null=True)
    
    # Social Links
    linkedin_url = models.URLField(blank=True, null=True)
    twitter_url = models.URLField(blank=True, null=True)
    website_url = models.URLField(blank=True, null=True)
    
    # Talk Details
    talk_title = models.CharField(max_length=200, blank=True, null=True)
    talk_abstract = models.TextField(blank=True, null=True)
    talk_duration = models.PositiveIntegerField(blank=True, null=True, help_text="Duration in minutes")
    
    order = models.PositiveIntegerField(default=0, help_text="Order in which speakers appear")
    
    class Meta:
        ordering = ['order', 'name']
    
    def __str__(self):
        return f"{self.name} - {self.event.title}"


class EventSchedule(models.Model):
    """Event schedule/agenda"""
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='schedule')
    title = models.CharField(max_length=200)
    description = models.TextField(blank=True, null=True)
    speaker = models.ForeignKey(EventSpeaker, on_delete=models.SET_NULL, null=True, blank=True)
    start_time = models.TimeField()
    end_time = models.TimeField()
    venue_details = models.CharField(max_length=200, blank=True, null=True)
    
    class Meta:
        ordering = ['start_time']
    
    def __str__(self):
        return f"{self.title} ({self.start_time} - {self.end_time})"


class EventFeedback(models.Model):
    """Event feedback from participants"""
    
    RATING_CHOICES = [
        (1, 'Poor'),
        (2, 'Fair'),
        (3, 'Good'),
        (4, 'Very Good'),
        (5, 'Excellent'),
    ]
    
    event = models.ForeignKey(Event, on_delete=models.CASCADE, related_name='feedback')
    registration = models.ForeignKey(EventRegistration, on_delete=models.CASCADE, related_name='feedback')
    
    # Ratings
    overall_rating = models.IntegerField(choices=RATING_CHOICES)
    content_rating = models.IntegerField(choices=RATING_CHOICES)
    organization_rating = models.IntegerField(choices=RATING_CHOICES)
    
    # Comments
    liked_most = models.TextField(blank=True, null=True)
    improvements = models.TextField(blank=True, null=True)
    additional_comments = models.TextField(blank=True, null=True)
    
    # Recommendations
    would_recommend = models.BooleanField(default=True)
    future_topics = models.TextField(blank=True, null=True)
    
    submitted_at = models.DateTimeField(auto_now_add=True)
    
    class Meta:
        unique_together = ['event', 'registration']
    
    def __str__(self):
        return f"Feedback for {self.event.title} by {self.registration.name}"


class Notification(models.Model):
    """Model for managing scrolling marquee notifications"""
    
    PRIORITY_CHOICES = [
        ('low', 'Low'),
        ('normal', 'Normal'),
        ('high', 'High'),
        ('urgent', 'Urgent'),
    ]
    
    TYPE_CHOICES = [
        ('info', 'Information'),
        ('warning', 'Warning'),
        ('success', 'Success'),
        ('error', 'Error'),
        ('event', 'Event'),
        ('announcement', 'Announcement'),
    ]
    
    # Content
    title = models.CharField(max_length=200, help_text="Brief notification title")
    message = models.TextField(help_text="Notification message content")
    
    # Categorization
    notification_type = models.CharField(
        max_length=20, 
        choices=TYPE_CHOICES, 
        default='info',
        help_text="Type of notification for styling"
    )
    priority = models.CharField(
        max_length=10, 
        choices=PRIORITY_CHOICES, 
        default='normal',
        help_text="Priority affects display order"
    )
    
    # Display Settings
    is_active = models.BooleanField(
        default=True, 
        help_text="Whether notification is currently displayed"
    )
    is_marquee = models.BooleanField(
        default=True, 
        help_text="Include in scrolling marquee"
    )
    display_duration = models.PositiveIntegerField(
        default=0, 
        help_text="Display duration in seconds (0 = permanent)"
    )
    
    # Scheduling
    start_date = models.DateTimeField(
        default=timezone.now,
        help_text="When notification becomes active"
    )
    end_date = models.DateTimeField(
        null=True, 
        blank=True,
        help_text="When notification expires (optional)"
    )
    
    # Links and Actions
    action_url = models.URLField(
        blank=True, 
        null=True,
        help_text="Optional link for 'Learn More' action"
    )
    action_text = models.CharField(
        max_length=50, 
        blank=True, 
        null=True,
        help_text="Text for action button"
    )
    
    # Styling
    background_color = models.CharField(
        max_length=7, 
        default='#007bff',
        help_text="Background color (hex code)"
    )
    text_color = models.CharField(
        max_length=7, 
        default='#ffffff',
        help_text="Text color (hex code)"
    )
    
    # Management
    created_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='created_notifications'
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    
    # Analytics
    view_count = models.PositiveIntegerField(default=0)
    click_count = models.PositiveIntegerField(default=0)
    
    class Meta:
        ordering = ['-priority', '-created_at']
        indexes = [
            models.Index(fields=['is_active', 'is_marquee']),
            models.Index(fields=['start_date', 'end_date']),
            models.Index(fields=['priority', 'notification_type']),
        ]
    
    def __str__(self):
        return f"{self.title} ({self.get_priority_display()})"
    
    @property
    def is_currently_active(self):
        """Check if notification is currently active based on dates"""
        now = timezone.now()
        if not self.is_active:
            return False
        if self.start_date > now:
            return False
        if self.end_date and self.end_date < now:
            return False
        return True
    
    @property
    def priority_weight(self):
        """Numeric weight for sorting by priority"""
        weights = {'low': 1, 'normal': 2, 'high': 3, 'urgent': 4}
        return weights.get(self.priority, 2)
    
    def increment_view_count(self):
        """Increment view count"""
        self.view_count += 1
        self.save(update_fields=['view_count'])
    
    def increment_click_count(self):
        """Increment click count"""
        self.click_count += 1
        self.save(update_fields=['click_count'])


class NotificationSettings(models.Model):
    """Global settings for notification system"""
    
    # Marquee Settings
    marquee_speed = models.PositiveIntegerField(
        default=50,
        help_text="Marquee scroll speed (pixels per second)"
    )
    marquee_pause_on_hover = models.BooleanField(
        default=True,
        help_text="Pause marquee when user hovers"
    )
    max_notifications_display = models.PositiveIntegerField(
        default=5,
        help_text="Maximum notifications to show in marquee"
    )
    
    # Display Settings
    show_date = models.BooleanField(
        default=True,
        help_text="Show notification date"
    )
    show_type_icon = models.BooleanField(
        default=True,
        help_text="Show type-specific icons"
    )
    enable_sound = models.BooleanField(
        default=False,
        help_text="Play sound for urgent notifications"
    )
    
    # Auto-refresh
    auto_refresh_interval = models.PositiveIntegerField(
        default=30,
        help_text="Auto-refresh interval in seconds"
    )
    
    # Management
    updated_by = models.ForeignKey(
        User, 
        on_delete=models.CASCADE, 
        related_name='notification_settings_updates'
    )
    updated_at = models.DateTimeField(auto_now=True)
    
    class Meta:
        verbose_name = "Notification Settings"
        verbose_name_plural = "Notification Settings"
    
    def __str__(self):
        return f"Notification Settings (Updated: {self.updated_at})"
    
    @classmethod
    def get_settings(cls):
        """Get current settings or create default"""
        settings = cls.objects.first()
        if not settings:
            # Create default settings with admin user
            admin_user = User.objects.filter(is_superuser=True).first()
            if admin_user:
                settings = cls.objects.create(updated_by=admin_user)
        return settings

