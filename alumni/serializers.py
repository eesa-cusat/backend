from rest_framework import serializers
from .models import Alumni
from django.contrib.auth import get_user_model

User = get_user_model()


class AlumniSerializer(serializers.ModelSerializer):
    years_since_graduation = serializers.ReadOnlyField()
    batch_name = serializers.ReadOnlyField()
    created_by_username = serializers.CharField(source='created_by.username', read_only=True)
    
    class Meta:
        model = Alumni
        fields = [
            'id', 'full_name', 'email', 'phone_number', 'alternative_phone',
            'student_id', 'scheme', 'year_of_joining', 'year_of_passout',
            'department', 'specialization', 'cgpa', 'job_title',
            'current_company', 'current_location', 'linkedin_profile',
            'employment_status', 'achievements',
            'feedback', 'willing_to_mentor', 'allow_contact_from_juniors',
            'newsletter_subscription', 'is_verified', 'is_active',
            'years_since_graduation', 'batch_name', 'created_by_username',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']
    
    def validate_email(self, value):
        """Ensure email is unique"""
        if self.instance and self.instance.email == value:
            return value
        if Alumni.objects.filter(email=value).exists():
            raise serializers.ValidationError("An alumni with this email already exists.")
        return value
    
    def validate_year_of_passout(self, value):
        """Validate year of passout"""
        from django.utils import timezone
        current_year = timezone.now().year
        if value > current_year:
            raise serializers.ValidationError("Year of passout cannot be in the future.")
        if value < 1950:
            raise serializers.ValidationError("Year of passout seems too old.")
        return value
    
    def validate(self, data):
        """Cross-field validation"""
        if 'year_of_joining' in data and 'year_of_passout' in data:
            if data['year_of_joining'] >= data['year_of_passout']:
                raise serializers.ValidationError(
                    "Year of joining must be before year of passout."
                )
        return data


class AlumniCreateSerializer(serializers.ModelSerializer):
    """Simplified serializer for bulk creation"""
    
    class Meta:
        model = Alumni
        fields = [
            'full_name', 'email', 'phone_number', 'student_id',
            'scheme', 'year_of_joining', 'year_of_passout',
            'department', 'specialization', 'cgpa',
            'job_title', 'current_company',
            'current_location', 'employment_status'
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
    year_wise_distribution = serializers.ListField(child=serializers.DictField())
    department_wise_distribution = serializers.ListField(child=serializers.DictField())


class AlumniSearchSerializer(serializers.Serializer):
    """Serializer for alumni search filters"""
    search = serializers.CharField(required=False, allow_blank=True)
    year_of_passout = serializers.IntegerField(required=False)
    department = serializers.CharField(required=False, allow_blank=True)
    employment_status = serializers.ChoiceField(
        choices=Alumni.EMPLOYMENT_STATUS_CHOICES, 
        required=False
    )
    current_company = serializers.CharField(required=False, allow_blank=True)
    willing_to_mentor = serializers.BooleanField(required=False)
    is_verified = serializers.BooleanField(required=False)
