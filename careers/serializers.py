from rest_framework import serializers
from .models import JobOpportunity, InternshipOpportunity, CertificateOpportunity

class JobOpportunitySerializer(serializers.ModelSerializer):
    posted_by = serializers.SerializerMethodField()
    requirements = serializers.SerializerMethodField()
    skills = serializers.SerializerMethodField()
    
    class Meta:
        model = JobOpportunity
        fields = [
            'id', 'title', 'company', 'location', 'job_type', 'experience_level',
            'description', 'requirements', 'skills', 'salary_range', 'application_url',
            'application_deadline', 'posted_by', 'posted_at', 'is_active'
        ]
    
    def get_posted_by(self, obj):
        return {
            'id': obj.posted_by.id,
            'username': obj.posted_by.username,
            'first_name': obj.posted_by.first_name,
            'last_name': obj.posted_by.last_name,
        }
    
    def get_requirements(self, obj):
        return obj.requirements_list
    
    def get_skills(self, obj):
        return obj.skills_list

class JobOpportunityCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = JobOpportunity
        fields = [
            'title', 'company', 'location', 'job_type', 'experience_level',
            'description', 'requirements', 'skills', 'salary_range', 
            'application_url', 'application_deadline'
        ]

class InternshipOpportunitySerializer(serializers.ModelSerializer):
    posted_by = serializers.SerializerMethodField()
    requirements = serializers.SerializerMethodField()
    skills = serializers.SerializerMethodField()
    
    class Meta:
        model = InternshipOpportunity
        fields = [
            'id', 'title', 'company', 'location', 'duration', 'internship_type',
            'description', 'requirements', 'skills', 'stipend_amount', 'application_url',
            'application_deadline', 'start_date', 'is_remote', 'certificate_provided',
            'letter_of_recommendation', 'posted_by', 'posted_at', 'is_active'
        ]
    
    def get_posted_by(self, obj):
        return {
            'id': obj.posted_by.id,
            'username': obj.posted_by.username,
            'first_name': obj.posted_by.first_name,
            'last_name': obj.posted_by.last_name,
        }
    
    def get_requirements(self, obj):
        return obj.requirements_list
    
    def get_skills(self, obj):
        return obj.skills_list

class InternshipOpportunityCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = InternshipOpportunity
        fields = [
            'title', 'company', 'location', 'duration', 'internship_type',
            'description', 'requirements', 'skills', 'stipend_amount', 
            'application_url', 'application_deadline', 'start_date', 'is_remote',
            'certificate_provided', 'letter_of_recommendation'
        ]

class CertificateOpportunitySerializer(serializers.ModelSerializer):
    posted_by = serializers.SerializerMethodField()
    prerequisites = serializers.SerializerMethodField()
    skills_covered = serializers.SerializerMethodField()
    
    class Meta:
        model = CertificateOpportunity
        fields = [
            'id', 'title', 'provider', 'certificate_type', 'description', 'duration',
            'prerequisites', 'skills_covered', 'is_free', 'price', 'financial_aid_available',
            'percentage_offer', 'validity_till', 'course_url', 'registration_deadline', 
            'start_date', 'industry_recognized', 'university_credit', 'posted_by', 
            'posted_at', 'is_active'
        ]
    
    def get_posted_by(self, obj):
        return {
            'id': obj.posted_by.id,
            'username': obj.posted_by.username,
            'first_name': obj.posted_by.first_name,
            'last_name': obj.posted_by.last_name,
        }
    
    def get_prerequisites(self, obj):
        return obj.prerequisites_list
    
    def get_skills_covered(self, obj):
        return obj.skills_list

class CertificateOpportunityCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CertificateOpportunity
        fields = [
            'title', 'provider', 'certificate_type', 'description', 'duration',
            'prerequisites', 'skills_covered', 'is_free', 'price', 'financial_aid_available',
            'percentage_offer', 'validity_till', 'course_url', 'registration_deadline', 
            'start_date', 'industry_recognized', 'university_credit'
        ]
