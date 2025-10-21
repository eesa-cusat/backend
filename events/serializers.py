from rest_framework import serializers
from .models import Event, EventRegistration, EventSpeaker, EventSchedule, EventFeedback, Notification, NotificationSettings


class EventSpeakerSerializer(serializers.ModelSerializer):
    """Serializer for event speakers"""
    class Meta:
        model = EventSpeaker
        fields = [
            'id', 'name', 'designation', 'organization', 'bio', 'profile_image',
            'linkedin_url', 'twitter_url', 'website_url', 'order'
        ]


class EventScheduleSerializer(serializers.ModelSerializer):
    # Support both old speaker FK and new speaker_name text field
    speaker = EventSpeakerSerializer(read_only=True)
    
    class Meta:
        model = EventSchedule
        fields = [
            'id', 'title', 'description', 'speaker_name', 'schedule_date', 
            'start_time', 'end_time', 'venue_details', 'speaker'
        ]


class EventSerializer(serializers.ModelSerializer):
    # Support both old EventSpeaker FK (for backwards compatibility) and new speaker_names JSON
    speakers = EventSpeakerSerializer(many=True, read_only=True)
    
    schedule = EventScheduleSerializer(many=True, read_only=True)
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    album = serializers.SerializerMethodField()
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
            'speakers', 'schedule', 'album',
            'is_upcoming', 'is_past', 'is_ongoing', 'is_registration_open',
            'registration_count', 'spots_remaining'
        ]
        read_only_fields = ['created_at', 'updated_at']
    
    def get_album(self, obj):
        """Get album with nested photos if available"""
        if hasattr(obj, 'album') and obj.album:
            # Import here to avoid circular import
            from gallery.serializers import AlbumSerializer
            return AlbumSerializer(obj.album, context=self.context).data
        return None
    
    def get_linked_gallery_album(self, obj):
        """Get linked gallery album basic info if available"""
        if obj.linked_gallery_album:
            return {
                'id': obj.linked_gallery_album.id,
                'slug': obj.linked_gallery_album.slug,
                'title': obj.linked_gallery_album.title
            }
        return None


class EventListSerializer(serializers.ModelSerializer):
    """Optimized serializer for event lists - includes all fields needed for cards"""
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    is_upcoming = serializers.ReadOnlyField()
    is_registration_open = serializers.ReadOnlyField()
    registration_count = serializers.ReadOnlyField()
    spots_remaining = serializers.ReadOnlyField()
    
    # Gallery information for backlink
    gallery_album_id = serializers.SerializerMethodField()
    photo_count = serializers.SerializerMethodField()
    
    class Meta:
        model = Event
        fields = [
            'id', 'title', 'description', 'event_type', 'status',
            'start_date', 'end_date', 'location', 'venue',
            'registration_required', 'max_participants', 'registration_fee',
            'banner_image', 'event_flyer',  # Add event_flyer to avoid secondary API calls
            'is_featured',
            'created_by_name', 'created_at',
            'is_upcoming', 'is_registration_open', 'registration_count', 'spots_remaining',
            'gallery_album_id', 'photo_count'
        ]
    
    def get_gallery_album_id(self, obj):
        """Get album ID if available"""
        return obj.album.id if hasattr(obj, 'album') and obj.album else None
    
    def get_photo_count(self, obj):
        """Get photo count if album exists"""
        return obj.album.photo_count if hasattr(obj, 'album') and obj.album else 0


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
            'payment_date', 'payment_reference_id',
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
