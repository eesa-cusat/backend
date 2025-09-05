from rest_framework import serializers
from .models import Alumni, AlumniBatch
from django.contrib.auth import get_user_model

User = get_user_model()


class AlumniBatchSerializer(serializers.ModelSerializer):
    """Serializer for Alumni Batch management"""
    employment_stats = serializers.ReadOnlyField()
    alumni_count = serializers.SerializerMethodField()
    graduation_year = serializers.ReadOnlyField()
    joining_year = serializers.ReadOnlyField()
    
    class Meta:
        model = AlumniBatch
        fields = [
            'id', 'batch_year_range', 'batch_name', 'batch_description',
            'total_alumni', 'verified_alumni', 'batch_group_photo',
            'employment_stats', 'alumni_count', 'graduation_year', 
            'joining_year', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'total_alumni', 'verified_alumni', 'created_at', 'updated_at']
    
    def get_alumni_count(self, obj):
        """Get count of alumni in this batch"""
        return obj.alumni_members.filter(is_active=True).count()
    
    def create(self, validated_data):
        """Create batch and auto-update statistics"""
        batch = super().create(validated_data)
        batch.update_statistics()
        return batch


class AlumniBatchListSerializer(serializers.ModelSerializer):
    """Simplified serializer for batch listing"""
    alumni_count = serializers.SerializerMethodField()
    
    class Meta:
        model = AlumniBatch
        fields = [
            'id', 'batch_year_range', 'batch_name', 'total_alumni', 
            'verified_alumni', 'batch_group_photo', 'alumni_count', 'created_at'
        ]
    
    def get_alumni_count(self, obj):
        return obj.alumni_members.filter(is_active=True).count()


class AlumniSerializer(serializers.ModelSerializer):
    """Simplified Alumni serializer focused on essential information"""
    years_since_graduation = serializers.ReadOnlyField()
    batch_name = serializers.ReadOnlyField()
    batch_details = serializers.SerializerMethodField()
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Alumni
        fields = [
            'id', 'full_name', 'email', 'phone_number', 'batch',
            'job_title', 'current_company', 'current_location', 
            'linkedin_profile', 'employment_status', 'achievements',
            'feedback', 'willing_to_mentor', 'allow_contact_from_juniors',
            'newsletter_subscription', 'is_verified', 'is_active',
            'years_since_graduation', 'batch_name', 'batch_details',
            'created_by_username', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def get_batch_details(self, obj):
        """Get detailed batch information"""
        if obj.batch:
            return {
                'id': obj.batch.id,
                'batch_year_range': obj.batch.batch_year_range,
                'batch_name': obj.batch.batch_name,
                'graduation_year': obj.batch.graduation_year,
                'joining_year': obj.batch.joining_year
            }
        return None
    
    def validate_email(self, value):
        """Ensure email is unique"""
        if self.instance and self.instance.email == value:
            return value
        if Alumni.objects.filter(email=value).exists():
            raise serializers.ValidationError("An alumni with this email already exists.")
        return value


class AlumniCreateSerializer(serializers.ModelSerializer):
    """Simplified serializer for bulk creation"""
    
    class Meta:
        model = Alumni
        fields = [
            'full_name', 'email', 'phone_number', 'batch',
            'job_title', 'current_company', 'current_location', 
            'employment_status'
        ]
    
    def validate_email(self, value):
        if Alumni.objects.filter(email=value).exists():
            raise serializers.ValidationError(f"Alumni with email {value} already exists.")
        return value


class BulkAlumniImportSerializer(serializers.Serializer):
    """Serializer for bulk CSV import"""
    csv_file = serializers.FileField()
    
    def validate_csv_file(self, value):
        if not value.name.endswith('.csv'):
            raise serializers.ValidationError("File must be a CSV file.")
        
        # Check file size (limit to 10MB)
        if value.size > 10 * 1024 * 1024:
            raise serializers.ValidationError("File size cannot exceed 10MB.")
        
        return value


class AlumniStatsSerializer(serializers.Serializer):
    """Serializer for alumni statistics"""
    total_alumni = serializers.IntegerField()
    employed_count = serializers.IntegerField()
    self_employed_count = serializers.IntegerField()
    higher_studies_count = serializers.IntegerField()
    unemployment_rate = serializers.FloatField()
    top_companies = serializers.ListField(child=serializers.DictField())
    batch_wise_distribution = serializers.ListField(child=serializers.DictField())


class AlumniBatchStatsSerializer(serializers.Serializer):
    """Serializer for batch statistics aggregation"""
    total_batches = serializers.IntegerField()
    total_alumni_across_batches = serializers.IntegerField()
    batches_with_photos = serializers.IntegerField()
    most_recent_batch = serializers.CharField(allow_null=True)
    oldest_batch = serializers.CharField(allow_null=True)
    batches_by_year = serializers.ListField(child=serializers.DictField())


class AlumniSearchSerializer(serializers.Serializer):
    """Serializer for alumni search filters"""
    search = serializers.CharField(required=False, allow_blank=True)
    batch = serializers.IntegerField(required=False)
    employment_status = serializers.ChoiceField(
        choices=Alumni.EMPLOYMENT_STATUS_CHOICES, 
        required=False
    )
    current_company = serializers.CharField(required=False, allow_blank=True)
    willing_to_mentor = serializers.BooleanField(required=False)
    is_verified = serializers.BooleanField(required=False)
