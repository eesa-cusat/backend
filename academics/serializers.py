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
