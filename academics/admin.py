from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.http import HttpResponseRedirect
from django.contrib import messages
from .models import Scheme, Subject, AcademicResource


@admin.register(Scheme)
class SchemeAdmin(admin.ModelAdmin):
    list_display = ['name', 'year', 'is_active', 'created_at']
    list_filter = ['year', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    list_editable = ['is_active']
    ordering = ['-year']


@admin.register(Subject)
class SubjectAdmin(admin.ModelAdmin):
    list_display = ['code', 'name', 'scheme', 'semester', 'credits', 'is_active']
    list_filter = ['scheme', 'semester', 'is_active', 'created_at']
    search_fields = ['code', 'name', 'scheme__name']
    list_editable = ['is_active']
    ordering = ['scheme__year', 'semester', 'code']


# Hide AcademicCategory from admin since we only have 5 fixed categories
# admin.site.unregister(AcademicCategory)


@admin.register(AcademicResource)
class AcademicResourceAdmin(admin.ModelAdmin):
    list_display = ['title', 'category', 'subject', 'scheme', 'is_approved', 'is_featured', 'uploaded_by', 'created_at', 'get_approval_status']
    list_filter = ['category', 'subject__scheme', 'is_approved', 'is_featured', 'uploaded_by', 'created_at']
    search_fields = ['title', 'description', 'subject__name', 'uploaded_by__username']
    list_editable = ['is_approved', 'is_featured']
    readonly_fields = ['uploaded_by', 'file_size', 'download_count', 'view_count', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    actions = ['approve_selected_resources', 'reject_selected_resources']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'category', 'subject')
        }),
        ('File Information', {
            'fields': ('file', 'file_size')
        }),
        ('Resource Details', {
            'fields': ('module_number', 'exam_type', 'exam_year', 'author', 'publisher', 'edition', 'isbn')
        }),
        ('Status & Statistics', {
            'fields': ('is_approved', 'is_featured', 'is_active', 'download_count', 'view_count')
        }),
        ('Metadata', {
            'fields': ('uploaded_by', 'approved_by', 'approved_at', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def scheme(self, obj):
        """Show scheme in list display"""
        return obj.subject.scheme.name if obj.subject else '-'
    scheme.short_description = 'Scheme'
    scheme.admin_order_field = 'subject__scheme__name'
    
    def get_approval_status(self, obj):
        """Show approval status with color coding"""
        if obj.is_approved:
            return format_html('<span style="color: green;">✓ Approved</span>')
        else:
            return format_html('<span style="color: orange;">⏳ Pending</span>')
    get_approval_status.short_description = 'Status'
    
    def get_queryset(self, request):
        """Show unverified notes first"""
        qs = super().get_queryset(request)
        return qs.select_related('subject', 'subject__scheme', 'uploaded_by').order_by('is_approved', '-created_at')
    
    def approve_selected_resources(self, request, queryset):
        """Admin action to approve selected resources"""
        updated = queryset.update(is_approved=True, approved_by=request.user)
        self.message_user(request, f'{updated} resources have been approved.')
    approve_selected_resources.short_description = "Approve selected resources"
    
    def reject_selected_resources(self, request, queryset):
        """Admin action to reject selected resources"""
        updated = queryset.update(is_approved=False, approved_by=None)
        self.message_user(request, f'{updated} resources have been rejected.')
    reject_selected_resources.short_description = "Reject selected resources"
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)


# AcademicCategory is not registered in admin, so it will not appear in the admin panel.
