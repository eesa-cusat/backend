from django.contrib import admin
from django.http import HttpResponse
from django.db.models import Count
import csv
from .models import Alumni, AlumniBatch


@admin.register(AlumniBatch)
class AlumniBatchAdmin(admin.ModelAdmin):
    list_display = [
        'batch_year_range', 'batch_name', 'total_alumni', 'verified_alumni', 
        'has_group_photo', 'created_at'
    ]
    list_filter = ['created_at']
    search_fields = ['batch_year_range', 'batch_name', 'batch_description']
    readonly_fields = ['total_alumni', 'verified_alumni', 'employment_stats', 'created_at', 'updated_at']
    ordering = ['-batch_year_range']
    
    fieldsets = (
        ('Batch Information', {
            'fields': ('batch_year_range', 'batch_name', 'batch_description')
        }),
        ('Batch Media', {
            'fields': ('batch_group_photo',),
            'description': 'Upload official graduation or group photos'
        }),
        ('Statistics', {
            'fields': ('total_alumni', 'verified_alumni', 'employment_stats'),
            'classes': ('collapse',),
            'description': 'Automatically computed from Alumni data'
        }),
        ('Timestamps', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def has_group_photo(self, obj):
        return bool(obj.batch_group_photo)
    has_group_photo.boolean = True
    has_group_photo.short_description = 'Has Photo'
    
    def save_model(self, request, obj, form, change):
        super().save_model(request, obj, form, change)
        # Update statistics after saving
        obj.update_statistics()


@admin.register(Alumni)
class AlumniAdmin(admin.ModelAdmin):
    list_display = [
        'id', 'full_name', 'email', 'batch', 'employment_status', 
        'current_company', 'is_verified', 'is_active', 'created_at'
    ]
    list_filter = [
        'batch', 'employment_status', 'is_verified', 
        'is_active', 'willing_to_mentor', 'created_at'
    ]
    search_fields = [
        'full_name', 'email', 'current_company',
        'job_title', 'batch__batch_name', 'batch__batch_year_range'
    ]
    readonly_fields = [
        'id', 'years_since_graduation', 'batch_name',
        'created_at', 'updated_at'
    ]
    ordering = ['id']
    
    fieldsets = (
        ('Personal Information', {
            'fields': (
                'full_name', 'email', 'phone_number'
            )
        }),
        ('Batch Information', {
            'fields': ('batch',),
            'description': 'Select the batch this alumni belongs to (e.g., 2019-2023, 2020-2024)'
        }),
        ('Current Status', {
            'fields': (
                'employment_status', 'job_title', 'current_company',
                'current_location', 'linkedin_profile'
            )
        }),
        ('Additional Information', {
            'fields': ('achievements', 'feedback'),
            'classes': ('collapse',)
        }),
        ('Contact Preferences', {
            'fields': (
                'willing_to_mentor', 'allow_contact_from_juniors',
                'newsletter_subscription'
            )
        }),
        ('Status', {
            'fields': ('is_verified', 'is_active')
        }),
        ('Computed Fields', {
            'fields': ('id', 'years_since_graduation', 'batch_name'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': (
                'created_by', 'created_at', 'updated_at'
            ),
            'classes': ('collapse',)
        })
    )
    
    actions = ['mark_as_verified', 'mark_as_unverified', 'export_as_csv']
    
    def mark_as_verified(self, request, queryset):
        updated = queryset.update(is_verified=True)
        self.message_user(request, f'{updated} alumni marked as verified.')
    mark_as_verified.short_description = "Mark selected alumni as verified"
    
    def mark_as_unverified(self, request, queryset):
        updated = queryset.update(is_verified=False)
        self.message_user(request, f'{updated} alumni marked as unverified.')
    mark_as_unverified.short_description = "Mark selected alumni as unverified"
    
    def export_as_csv(self, request, queryset):
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="alumni_export.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'ID', 'Full Name', 'Email', 'Phone', 'Batch Year Range',
            'Batch Name', 'Current Company', 'Job Title',
            'Employment Status', 'LinkedIn', 'Willing to Mentor', 'Is Verified'
        ])
        
        for alumni in queryset.select_related('batch'):
            writer.writerow([
                alumni.id, alumni.full_name, alumni.email, alumni.phone_number,
                alumni.batch.batch_year_range if alumni.batch else '',
                alumni.batch.batch_name if alumni.batch else '',
                alumni.current_company, alumni.job_title,
                alumni.employment_status, alumni.linkedin_profile,
                alumni.willing_to_mentor, alumni.is_verified
            ])
        
        return response
    export_as_csv.short_description = "Export selected alumni as CSV"
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by', 'batch')
    
    def save_model(self, request, obj, form, change):
        if not change:  # Creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
        
        # Update batch statistics if batch is set
        if obj.batch:
            obj.batch.update_statistics()
