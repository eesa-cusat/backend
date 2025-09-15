from rest_framework import serializers
from django.utils import timezone
from .models import Subject, AcademicResource, Scheme

class SchemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scheme
        fields = ['id', 'name', 'year', 'is_active', 'created_at']

class CreateSchemeSerializer(serializers.ModelSerializer):
    class Meta:
        model = Scheme
        fields = ['name', 'year', 'is_active']

class CreateSubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['name', 'code', 'scheme', 'semester', 'department', 'credits', 'is_active']

class SubjectSerializer(serializers.ModelSerializer):
    class Meta:
        model = Subject
        fields = ['id', 'name', 'code', 'scheme', 'department', 'semester', 'is_active']

class AcademicResourceListSerializer(serializers.ModelSerializer):
    """Lightweight serializer for resource listing with minimal queries"""
    subject_name = serializers.CharField(source='subject.name', read_only=True)
    subject_code = serializers.CharField(source='subject.code', read_only=True)
    subject_department = serializers.CharField(source='subject.department', read_only=True)
    subject_semester = serializers.IntegerField(source='subject.semester', read_only=True)
    scheme_name = serializers.CharField(source='subject.scheme.name', read_only=True)
    scheme_year = serializers.IntegerField(source='subject.scheme.year', read_only=True)
    uploaded_by_name = serializers.SerializerMethodField()
    file_url = serializers.SerializerMethodField()
    file_size_mb = serializers.SerializerMethodField()

    class Meta:
        model = AcademicResource
        fields = [
            'id', 'title', 'description', 'category', 'file_url',
            'file_size_mb', 'module_number', 'like_count', 'download_count',
            'created_at', 'subject_name', 'subject_code', 'subject_department',
            'subject_semester', 'scheme_name', 'scheme_year', 'uploaded_by_name'
        ]

    def get_uploaded_by_name(self, obj):
        if obj.uploaded_by:
            return f"{obj.uploaded_by.first_name} {obj.uploaded_by.last_name}".strip() or obj.uploaded_by.username
        return "Anonymous"

    def get_file_url(self, obj):
        if obj.file:
            return obj.file.url
        return None

    def get_file_size_mb(self, obj):
        if obj.file_size:
            return round(obj.file_size / (1024 * 1024), 2)
        return 0


class AcademicResourceSerializer(serializers.ModelSerializer):
    uploaded_by = serializers.PrimaryKeyRelatedField(read_only=True)
    file = serializers.FileField()
    title = serializers.CharField(required=True)

    class Meta:
        model = AcademicResource
        fields = [
            'id', 'title', 'description', 'category', 'subject', 'file',
            'module_number', 'uploaded_by', 'approved_by', 'is_approved',
            'download_count', 'like_count', 'is_active', 'created_at'
        ]
        read_only_fields = [
            'uploaded_by', 'is_approved', 'approved_by', 'approved_at',
            'download_count', 'view_count', 'is_featured', 'is_active',
            'created_at', 'updated_at'
        ]

    def validate_file(self, value):
        # Only allow PDF files
        if not value.name.lower().endswith('.pdf'):
            raise serializers.ValidationError('Only PDF files are allowed.')
        # Limit file size to 15MB
        if value.size > 15 * 1024 * 1024:
            raise serializers.ValidationError('File size must be less than 15MB.')
        return value


class AcademicResourceAdminSerializer(serializers.ModelSerializer):
    """Admin serializer that allows updating approval status and other admin fields"""
    uploaded_by = serializers.PrimaryKeyRelatedField(read_only=True)
    file = serializers.FileField(required=False)
    title = serializers.CharField(required=True)

    class Meta:
        model = AcademicResource
        fields = [
            'id', 'title', 'description', 'category', 'subject', 'file',
            'module_number', 'uploaded_by', 'approved_by', 'is_approved',
            'download_count', 'like_count', 'is_active', 'created_at'
        ]
        read_only_fields = [
            'uploaded_by', 'approved_by', 'approved_at',
            'download_count', 'view_count', 'is_featured',
            'created_at', 'updated_at'
        ]

    def validate_file(self, value):
        if value:  # Only validate if file is provided
            # Only allow PDF files
            if not value.name.lower().endswith('.pdf'):
                raise serializers.ValidationError('Only PDF files are allowed.')
            # Limit file size to 15MB
            if value.size > 15 * 1024 * 1024:
                raise serializers.ValidationError('File size must be less than 15MB.')
        return value

    def update(self, instance, validated_data):
        """Custom update method to handle approval status changes"""
        is_approved = validated_data.get('is_approved')
        
        # If approval status is being changed, update related fields
        if is_approved is not None and instance.is_approved != is_approved:
            if is_approved:
                # Being approved
                validated_data['approved_by'] = self.context['request'].user
                validated_data['approved_at'] = timezone.now()
            else:
                # Being unapproved
                validated_data['approved_by'] = None
                validated_data['approved_at'] = None
        
        return super().update(instance, validated_data)
