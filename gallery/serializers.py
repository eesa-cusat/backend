from rest_framework import serializers
from .models import Album, Photo
from events.models import Event


class PhotoSerializer(serializers.ModelSerializer):
    """Serializer for Gallery Photos"""
    
    uploaded_by_name = serializers.CharField(source='uploaded_by.get_full_name', read_only=True)
    
    class Meta:
        model = Photo
        fields = [
            'id',
            'image',
            'caption', 
            'uploaded_at',
            'uploaded_by',
            'uploaded_by_name'
        ]
        read_only_fields = ['uploaded_by', 'uploaded_at']
    
    def create(self, validated_data):
        validated_data['uploaded_by'] = self.context['request'].user
        return super().create(validated_data)


class AlbumSerializer(serializers.ModelSerializer):
    """Serializer for Gallery Albums with nested photos"""
    
    photos = PhotoSerializer(many=True, read_only=True)
    photo_count = serializers.ReadOnlyField()
    created_by_name = serializers.CharField(source='created_by.get_full_name', read_only=True)
    event_title = serializers.CharField(source='event.title', read_only=True)
    batch_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Album
        fields = [
            'id',
            'name',
            'type',
            'description',
            'cover_image',
            'event',
            'batch_year',
            'event_title',
            'batch_info',
            'created_at',
            'created_by',
            'created_by_name',
            'photo_count',
            'photos'
        ]
        read_only_fields = ['created_by', 'created_at', 'photo_count']
    
    def get_batch_info(self, obj):
        """Get alumni batch information for alumni albums"""
        if obj.type == 'alumni' and obj.batch_year:
            # Import here to avoid circular imports
            from alumni.models import AlumniBatch
            try:
                batch = AlumniBatch.objects.get(year=obj.batch_year)
                return {
                    'year': batch.year,
                    'batch_name': batch.batch_name,
                    'total_alumni': batch.total_alumni,
                    'verified_alumni': batch.verified_alumni
                }
            except AlumniBatch.DoesNotExist:
                return {
                    'year': obj.batch_year,
                    'batch_name': f"Batch {obj.batch_year}",
                    'total_alumni': 0,
                    'verified_alumni': 0
                }
        return None
    
    def validate(self, data):
        """Custom validation for album creation"""
        album_type = data.get('type')
        event = data.get('event')
        batch_year = data.get('batch_year')
        
        # EESA albums must be linked to an event
        if album_type == 'eesa' and not event:
            raise serializers.ValidationError("EESA albums must be linked to an event.")
        
        # General albums cannot be linked to events or batches
        if album_type == 'general' and event:
            raise serializers.ValidationError("General albums cannot be linked to events.")
        if album_type == 'general' and batch_year:
            raise serializers.ValidationError("General albums cannot have batch years.")
        
        # Alumni albums must have batch year and cannot be linked to events
        if album_type == 'alumni' and not batch_year:
            raise serializers.ValidationError("Alumni albums must have a batch year.")
        if album_type == 'alumni' and event:
            raise serializers.ValidationError("Alumni albums cannot be linked to events.")
        
        # Check if event already has an album (for updates)
        if event:
            existing_album = Album.objects.filter(event=event).exclude(
                id=self.instance.id if self.instance else None
            ).first()
            if existing_album:
                raise serializers.ValidationError("This event already has an album.")
        
        # Check if batch year already has an album (for alumni type)
        if album_type == 'alumni' and batch_year:
            existing_album = Album.objects.filter(type='alumni', batch_year=batch_year).exclude(
                id=self.instance.id if self.instance else None
            ).first()
            if existing_album:
                raise serializers.ValidationError(f"Batch {batch_year} already has an album.")
        
        return data
    
    def create(self, validated_data):
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)


class AlbumListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for album listings"""
    
    photo_count = serializers.ReadOnlyField()
    event_title = serializers.CharField(source='event.title', read_only=True)
    batch_info = serializers.SerializerMethodField()
    
    class Meta:
        model = Album
        fields = [
            'id',
            'name', 
            'type',
            'description',
            'cover_image',
            'event_title',
            'batch_year',
            'batch_info',
            'created_at',
            'photo_count'
        ]
    
    def get_batch_info(self, obj):
        """Get simplified batch info for alumni albums"""
        if obj.type == 'alumni' and obj.batch_year:
            return {
                'year': obj.batch_year,
                'batch_name': f"Batch {obj.batch_year}"
            }
        return None
