from django.contrib import admin
from .models import JobOpportunity, InternshipOpportunity, CertificateOpportunity

@admin.register(JobOpportunity)
class JobOpportunityAdmin(admin.ModelAdmin):
    list_display = ['title', 'company', 'job_type', 'experience_level', 'location', 'posted_by', 'posted_at', 'is_active']
    list_filter = ['job_type', 'experience_level', 'is_active', 'posted_at']
    search_fields = ['title', 'company', 'location', 'description']
    readonly_fields = ['posted_at', 'created_at', 'updated_at']
    list_editable = ['is_active']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'company', 'location', 'job_type', 'experience_level')
        }),
        ('Job Details', {
            'fields': ('description', 'requirements', 'skills', 'salary_range')
        }),
        ('Application', {
            'fields': ('application_url', 'application_deadline')
        }),
        ('Meta', {
            'fields': ('posted_by', 'is_active', 'posted_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(InternshipOpportunity)
class InternshipOpportunityAdmin(admin.ModelAdmin):
    list_display = ['title', 'company', 'duration', 'internship_type', 'location', 'is_remote', 'posted_by', 'posted_at', 'is_active']
    list_filter = ['duration', 'internship_type', 'is_remote', 'certificate_provided', 'is_active', 'posted_at']
    search_fields = ['title', 'company', 'location', 'description']
    readonly_fields = ['posted_at', 'created_at', 'updated_at']
    list_editable = ['is_active']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'company', 'location', 'duration', 'internship_type')
        }),
        ('Internship Details', {
            'fields': ('description', 'requirements', 'skills', 'stipend_amount', 'start_date')
        }),
        ('Benefits & Features', {
            'fields': ('is_remote', 'certificate_provided', 'letter_of_recommendation')
        }),
        ('Application', {
            'fields': ('application_url', 'application_deadline')
        }),
        ('Meta', {
            'fields': ('posted_by', 'is_active', 'posted_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )

@admin.register(CertificateOpportunity)
class CertificateOpportunityAdmin(admin.ModelAdmin):
    list_display = ['title', 'provider', 'certificate_type', 'is_free', 'university_credit', 'percentage_offer', 'validity_till', 'industry_recognized', 'posted_by', 'posted_at', 'is_active']
    list_filter = ['provider', 'certificate_type', 'is_free', 'industry_recognized', 'university_credit', 'financial_aid_available', 'is_active', 'posted_at']
    search_fields = ['title', 'provider', 'description', 'skills_covered']
    readonly_fields = ['posted_at', 'created_at', 'updated_at']
    list_editable = ['is_active']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'provider', 'certificate_type', 'duration')
        }),
        ('Course Details', {
            'fields': ('description', 'prerequisites', 'skills_covered')
        }),
        ('Pricing & Access', {
            'fields': ('is_free', 'price', 'financial_aid_available', 'percentage_offer', 'validity_till')
        }),
        ('Schedule & Links', {
            'fields': ('course_url', 'registration_deadline', 'start_date')
        }),
        ('University Credits', {
            'fields': ('industry_recognized', 'university_credit', 'credit_hours'),
            'description': 'Only enter credit hours if university credit is checked. The form will validate this automatically.'
        }),
        ('Meta', {
            'fields': ('posted_by', 'is_active', 'posted_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        }),
    )
        
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        return form
