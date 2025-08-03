from rest_framework import serializers
from .models import Event, EventRegistration, EventSpeaker, EventSchedule, EventFeedback, Notification, NotificationSettings


class EventSpeakerSerializer(serializers.ModelSerializer):
    class Meta:
        model = EventSpeaker
        fields = [
            'id', 'name', 'title', 'organization', 'bio', 'profile_image',
            'linkedin_url', 'twitter_url', 'website_url',
            'talk_title', 'talk_abstract', 'talk_duration', 'order'
        ]


class EventScheduleSerializer(serializers.ModelSerializer):
    speaker = EventSpeakerSerializer(read_only=True)
    
    class Meta:
        model = EventSchedule
        fields = [
            'id', 'title', 'description', 'speaker', 'start_time', 'end_time', 'venue_details'
        ]


class EventSerializer(serializers.ModelSerializer):
    speakers = EventSpeakerSerializer(many=True, read_only=True)
    schedule = EventScheduleSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    
    # Dynamic properties
    is_upcoming = serializers.ReadOnlyField()
    is_past = serializers.ReadOnlyField()
    is_ongoing = serializers.ReadOnlyField()
    is_registration_open = serializers.ReadOnlyField()
    registration_count = serializers.ReadOnlyField()
    spots_remaining = serializers.ReadOnlyField()
    
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'event_type', 'status',
            'start_date', 'end_date', 'registration_deadline',
            'location', 'venue', 'address', 'is_online', 'meeting_link',
            'registration_required', 'max_participants',
            'registration_fee', 'payment_required', 'payment_qr_code',
            'payment_upi_id', 'payment_instructions',
            'contact_person', 'contact_email', 'contact_phone',
            'banner_image', 'event_flyer',
            'is_active', 'is_featured',
            'created_by_name', 'created_at', 'updated_at',
            'speakers', 'schedule',
            'is_upcoming', 'is_past', 'is_ongoing', 'is_registration_open',
            'registration_count', 'spots_remaining'
        ]
        read_only_fields = ['created_at', 'updated_at']


class EventListSerializer(serializers.ModelSerializer):
    """Simplified serializer for event lists"""
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    is_upcoming = serializers.ReadOnlyField()
    is_registration_open = serializers.ReadOnlyField()
    registration_count = serializers.ReadOnlyField()
    spots_remaining = serializers.ReadOnlyField()
    
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'event_type', 'status',
            'start_date', 'end_date', 'location', 'venue',
            'registration_required', 'max_participants', 'registration_fee',
            'banner_image', 'is_featured',
            'created_by_name', 'created_at',
            'is_upcoming', 'is_registration_open', 'registration_count', 'spots_remaining'
        ]


class EventRegistrationSerializer(serializers.ModelSerializer):
    event_title = serializers.CharField(source='event.title', read_only=True)
    event_date = serializers.DateTimeField(source='event.start_date', read_only=True)
    payment_status_display = serializers.CharField(source='get_payment_status_display', read_only=True)
    
    class Meta:
        model = EventRegistration
        fields = [
            'id', 'event', 'event_title', 'event_date',
            'name', 'email', 'mobile_number',
            'institution', 'department', 'year_of_study',
            'organization', 'designation',
            'payment_status', 'payment_status_display', 'payment_amount',
            'payment_date', 'payment_reference',
            'dietary_requirements', 'special_needs',
            'attended', 'certificate_issued',
            'registered_at', 'updated_at'
        ]
        read_only_fields = ['registered_at', 'updated_at', 'payment_amount']
    
    def validate_email(self, value):
        """Ensure email is unique per event"""
        event = self.initial_data.get('event')
        if event:
            existing = EventRegistration.objects.filter(
                event_id=event, email=value
            ).exclude(id=self.instance.id if self.instance else None)
            if existing.exists():
                raise serializers.ValidationError("You have already registered for this event.")
        return value
    
    def validate(self, data):
        """Validate registration constraints"""
        event = data.get('event')
        if event:
            # Check if registration is open
            if not event.is_registration_open:
                raise serializers.ValidationError("Registration is closed for this event.")
            
            # Check if event is published
            if event.status != 'published':
                raise serializers.ValidationError("Registration is not available for this event.")
        
        return data


class EventFeedbackSerializer(serializers.ModelSerializer):
    event_title = serializers.CharField(source='event.title', read_only=True)
    participant_name = serializers.CharField(source='registration.name', read_only=True)
    
    class Meta:
        model = EventFeedback
        fields = [
            'id', 'event', 'event_title', 'registration', 'participant_name',
            'overall_rating', 'content_rating', 'organization_rating',
            'liked_most', 'improvements', 'additional_comments',
            'would_recommend', 'future_topics',
            'submitted_at'
        ]
        read_only_fields = ['submitted_at']
    
    def validate(self, data):
        """Ensure participant has attended the event"""
        registration = data.get('registration')
        if registration and not registration.attended:
            raise serializers.ValidationError("Feedback can only be submitted by participants who attended the event.")
        return data


class EventRegistrationCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating event registrations (event field is set automatically)"""
    
    class Meta:
        model = EventRegistration
        fields = [
            'name', 'email', 'mobile_number',
            'institution', 'department', 'year_of_study',
            'organization', 'designation',
            'dietary_requirements', 'special_needs'
        ]
    
    def validate_email(self, value):
        """Ensure email is unique per event"""
        # We can't check here since we don't have access to the event yet
        # This validation will be done in the view
        return value


class NotificationSerializer(serializers.ModelSerializer):
    """Serializer for Notification model"""
    
    created_by_name = serializers.SerializerMethodField()
    is_currently_active = serializers.ReadOnlyField()
    priority_display = serializers.CharField(source='get_priority_display', read_only=True)
    type_display = serializers.CharField(source='get_notification_type_display', read_only=True)
    
    class Meta:
        model = Notification
        fields = [
            'id', 'title', 'message', 'notification_type', 'type_display',
            'priority', 'priority_display', 'is_active', 'is_marquee',
            'display_duration', 'start_date', 'end_date', 'action_url',
            'action_text', 'background_color', 'text_color', 'created_by_name',
            'created_at', 'updated_at', 'view_count', 'click_count',
            'is_currently_active'
        ]
    
    def get_created_by_name(self, obj):
        """Get creator's full name or username"""
        if obj.created_by:
            full_name = f"{obj.created_by.first_name} {obj.created_by.last_name}".strip()
            return full_name if full_name else obj.created_by.username
        return None


class NotificationSettingsSerializer(serializers.ModelSerializer):
    """Serializer for NotificationSettings model"""
    
    updated_by_name = serializers.SerializerMethodField()
    
    class Meta:
        model = NotificationSettings
        fields = [
            'id', 'marquee_speed', 'marquee_pause_on_hover', 
            'max_notifications_display', 'show_date', 'show_type_icon',
            'enable_sound', 'auto_refresh_interval', 'updated_by_name',
            'updated_at'
        ]
    
    def get_updated_by_name(self, obj):
        """Get updater's full name or username"""
        if obj.updated_by:
            full_name = f"{obj.updated_by.first_name} {obj.updated_by.last_name}".strip()
            return full_name if full_name else obj.updated_by.username
        return None
