from rest_framework import serializers
from .models import Subject, AcademicResource

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
            'module_number', 'exam_type', 'exam_year', 'author', 'publisher',
            'edition', 'isbn', 'uploaded_by', 'is_approved', 'approved_by',
            'approved_at', 'download_count', 'view_count', 'is_featured',
            'is_active', 'created_at', 'updated_at'
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
