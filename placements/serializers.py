from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Company, PlacementDrive, PlacementApplication, StudentCoordinator, PlacementStatistics, PlacedStudent

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Simple user serializer for references"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id', 'username', 'email']


class CompanySerializer(serializers.ModelSerializer):
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = Company
        fields = [
            'id', 'name', 'description', 'website', 'logo', 'industry', 
            'location', 'company_size', 'contact_person', 'contact_email', 
            'contact_phone', 'is_active', 'is_verified', 'created_at', 
            'updated_at', 'created_by'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']


class PlacementDriveSerializer(serializers.ModelSerializer):
    company = CompanySerializer(read_only=True)
    company_id = serializers.IntegerField(write_only=True)
    created_by = UserSerializer(read_only=True)
    is_registration_open = serializers.ReadOnlyField()
    is_upcoming = serializers.ReadOnlyField()
    applications_count = serializers.SerializerMethodField()
    
    class Meta:
        model = PlacementDrive
        fields = [
            'id', 'company', 'company_id', 'title', 'description', 'job_type',
            'min_cgpa', 'min_percentage', 'eligible_batches',
            'package_lpa', 'package_details', 'registration_start', 'registration_end',
            'drive_date', 'result_date', 'location', 'drive_mode', 'application_link',
            'required_documents', 'additional_info', 'is_active', 'is_featured', 
            'created_at', 'updated_at', 'created_by', 'is_registration_open', 
            'is_upcoming', 'applications_count'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']
    
    def get_applications_count(self, obj):
        return obj.applications.count()
    
    def validate(self, data):
        """Validate drive dates"""
        if data['registration_start'] >= data['registration_end']:
            raise serializers.ValidationError("Registration start must be before registration end")
        
        if data['registration_end'] >= data['drive_date']:
            raise serializers.ValidationError("Registration end must be before drive date")
        
        return data


class PlacementApplicationSerializer(serializers.ModelSerializer):
    drive = PlacementDriveSerializer(read_only=True)
    drive_id = serializers.IntegerField(write_only=True)
    student = UserSerializer(read_only=True)
    student_name = serializers.SerializerMethodField()
    company_name = serializers.SerializerMethodField()
    
    class Meta:
        model = PlacementApplication
        fields = [
            'id', 'drive', 'drive_id', 'student', 'student_name', 'company_name',
            'status', 'cover_letter', 'resume', 'additional_documents',
            'interview_date', 'interview_mode', 'interview_notes',
            'result_status', 'feedback', 'applied_at', 'updated_at'
        ]
        read_only_fields = ['id', 'applied_at', 'updated_at', 'student']
    
    def get_student_name(self, obj):
        return obj.student.get_full_name()
    
    def get_company_name(self, obj):
        return obj.drive.company.name


class StudentCoordinatorSerializer(serializers.ModelSerializer):
    user_details = UserSerializer(source='user', read_only=True)
    
    class Meta:
        model = StudentCoordinator
        fields = [
            'id', 'user', 'user_details', 'designation', 'profile_picture', 
            'mobile_number', 'email', 'bio', 'is_active', 'display_order', 
            'created_at', 'updated_at'
        ]


class PlacementStatisticsSerializer(serializers.ModelSerializer):
    placement_percentage = serializers.ReadOnlyField()
    
    class Meta:
        model = PlacementStatistics
        fields = [
            'id', 'academic_year', 'batch_year', 'branch', 'total_students',
            'total_placed', 'highest_package', 'average_package', 'median_package',
            'total_companies_visited', 'total_offers', 'placement_percentage',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at']


# Simplified serializers for lists and dropdowns
class CompanyListSerializer(serializers.ModelSerializer):
    class Meta:
        model = Company
        fields = ['id', 'name', 'logo', 'industry', 'location', 'is_verified']


class PlacementDriveListSerializer(serializers.ModelSerializer):
    company_name = serializers.CharField(source='company.name', read_only=True)
    company_logo = serializers.ImageField(source='company.logo', read_only=True)
    is_registration_open = serializers.ReadOnlyField()
    
    class Meta:
        model = PlacementDrive
        fields = [
            'id', 'title', 'company_name', 'company_logo', 'job_type',
            'package_lpa', 'registration_end', 'drive_date', 'location',
            'is_registration_open', 'is_featured'
        ]


class PlacementApplicationListSerializer(serializers.ModelSerializer):
    drive_title = serializers.CharField(source='drive.title', read_only=True)
    company_name = serializers.CharField(source='drive.company.name', read_only=True)
    student_name = serializers.SerializerMethodField()
    
    class Meta:
        model = PlacementApplication
        fields = [
            'id', 'drive_title', 'company_name', 'student_name', 'status',
            'result_status', 'applied_at', 'interview_date'
        ]
    
    def get_student_name(self, obj):
        return obj.student.get_full_name()


class PlacedStudentSerializer(serializers.ModelSerializer):
    """Full placed student serializer"""
    
    company_details = CompanySerializer(source='company', read_only=True)
    created_by = UserSerializer(read_only=True)
    
    class Meta:
        model = PlacedStudent
        fields = [
            'id', 'student_name', 'student_email', 'roll_number', 'branch',
            'batch_year', 'cgpa', 'company', 'company_details', 'placement_drive',
            'job_title', 'package_lpa', 'package_details', 'work_location',
            'job_type', 'offer_date', 'joining_date', 'offer_letter',
            'student_photo', 'testimonial', 'is_verified', 'is_active',
            'created_at', 'updated_at', 'created_by'
        ]
        read_only_fields = ['id', 'created_at', 'updated_at', 'created_by']


class PlacedStudentListSerializer(serializers.ModelSerializer):
    """Simplified placed student serializer for lists"""
    
    company_name = serializers.CharField(source='company.name', read_only=True)
    company_logo = serializers.ImageField(source='company.logo', read_only=True)
    job_type_display = serializers.CharField(source='get_job_type_display', read_only=True)
    
    class Meta:
        model = PlacedStudent
        fields = [
            'id', 'student_name', 'branch', 'batch_year', 'cgpa',
            'company_name', 'company_logo', 'job_title', 'package_lpa',
            'work_location', 'job_type', 'job_type_display', 'offer_date',
            'is_verified', 'created_at'
        ]
