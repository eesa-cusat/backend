from django.contrib import admin
from django.utils.html import format_html
from .models import Scheme, Subject, AcademicResource


@admin.register(Scheme)
class SchemeAdmin(admin.ModelAdmin):
    list_display = ['name', 'year', 'is_active', 'created_at']
    list_filter = ['year', 'is_active']
    search_fields = ['name']
    list_editable = ['is_active']
    ordering = ['-year']


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'scheme', 'semester', 'department', 'is_active']
    list_filter = ['scheme', 'semester', 'department', 'is_active']
    search_fields = ['code', 'name', 'scheme__name']
    list_editable = ['is_active']
    ordering = ['scheme__year', 'semester', 'code']
    fields = ['name', 'code', 'scheme', 'department', 'semester', 'is_active']


# Hide AcademicCategory from admin since we only have 5 fixed categories
# admin.site.unregister(AcademicCategory)


@admin.register(AcademicResource)
class AcademicResourceAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'category', 'subject', 'module_number',
        'uploaded_by', 'is_approved', 'created_at', 'file_link'
    ]
    list_filter = [
        'category', 'subject__scheme', 'subject__department',
        'module_number', 'is_approved', 'is_active'
    ]
    search_fields = [
        'title', 'description', 'subject__name',
        'subject__code'
    ]
    list_editable = ['is_approved']
    readonly_fields = [
        'uploaded_by', 'approved_by', 'file_size', 'download_count',
        'like_count', 'created_at', 'file_link'
    ]
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'category', 'subject')
        }),
        ('File Information', {
            'fields': ('file', 'file_size', 'file_link')
        }),
        ('Resource Details', {
            'fields': ('module_number',)
        }),
        ('Status & Statistics', {
            'fields': (
                'is_approved', 'is_active',
                'download_count', 'like_count'
            )
        }),
        ('Metadata', {
            'fields': ('uploaded_by', 'approved_by', 'created_at'),
            'classes': ('collapse',)
        })
    )

    def file_link(self, obj):
        if obj.file:
            return format_html('<a href="{}" target="_blank">View File</a>', obj.file.url)
        return "No file uploaded"
    file_link.short_description = "File"

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.uploaded_by = request.user
        if 'is_approved' in form.changed_data and obj.is_approved:
            obj.approved_by = request.user
        super().save_model(request, obj, form, change)


# AcademicCategory is not registered in admin, so it will not appear in the admin panel.
