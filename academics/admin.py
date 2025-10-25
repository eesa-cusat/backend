from django.contrib import admin
from django.utils.html import format_html
from django.urls import path, reverse
from django.shortcuts import render, redirect
from django.contrib import messages
from django.http import JsonResponse
from django.views.decorators.http import require_http_methods
from django.contrib.admin.views.decorators import staff_member_required
from django.db import transaction
import json
from .models import Scheme, Subject, AcademicResource, DEPARTMENT_CHOICES, SEMESTER_CHOICES


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
    list_filter = ['scheme', 'department', 'semester', 'is_active']
    search_fields = ['code', 'name', 'scheme__name']
    list_editable = ['is_active']
    ordering = ['scheme__year', 'semester', 'code']
    fields = ['name', 'code', 'scheme', 'department', 'semester', 'is_active']
    
    def formfield_for_foreignkey(self, db_field, request, **kwargs):
        """Optimize foreign key queries"""
        if db_field.name == "scheme":
            kwargs["queryset"] = Scheme.objects.filter(is_active=True).order_by('-year')
        return super().formfield_for_foreignkey(db_field, request, **kwargs)


# Hide AcademicCategory from admin since we only have 5 fixed categories
# admin.site.unregister(AcademicCategory)


@admin.register(AcademicResource)
class AcademicResourceAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'category_badge', 'subject_info', 'module_badge',
        'uploaded_by', 'approval_status', 'is_approved', 'stats_display', 'created_at', 'file_link'
    ]
    list_filter = [
        'category', 'subject__scheme', 'subject__department',
        'subject__semester', 'module_number', 'is_approved', 'is_active'
    ]
    search_fields = [
        'title', 'description', 'subject__name',
        'subject__code', 'uploaded_by__username'
    ]
    list_editable = ['is_approved']
    readonly_fields = [
        'uploaded_by', 'approved_by', 'file_size', 'download_count',
        'like_count', 'created_at', 'file_preview'
    ]
    actions = ['approve_resources', 'reject_resources', 'activate_resources', 'deactivate_resources']
    list_per_page = 25
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('📚 Basic Information', {
            'fields': ('title', 'description', 'category', 'subject'),
            'description': 'Core information about the academic resource'
        }),
        ('📄 File Management', {
            'fields': ('file', 'file_size', 'file_preview'),
            'description': 'Upload and manage the resource file'
        }),
        ('🎯 Resource Classification', {
            'fields': ('module_number',),
            'description': 'Organize by module/unit number (1-6)'
        }),
        ('✅ Approval & Status', {
            'fields': ('is_approved', 'is_active', 'approved_by'),
            'description': 'Manage resource approval and visibility'
        }),
        ('📊 Analytics & Engagement', {
            'fields': ('download_count', 'like_count'),
            'classes': ('collapse',)
        }),
        ('🕐 Metadata', {
            'fields': ('uploaded_by', 'created_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_queryset(self, request):
        """Optimize queries with select_related and prefetch_related"""
        qs = super().get_queryset(request)
        return qs.select_related(
            'subject', 'subject__scheme', 'uploaded_by', 'approved_by'
        )
    
    def category_badge(self, obj):
        """Display category with color-coded badge"""
        colors = {
            'notes': '#3498db',
            'textbook': '#e74c3c',
            'question_paper': '#9b59b6',
            'lab_manual': '#f39c12',
            'syllabus': '#27ae60'
        }
        color = colors.get(obj.category, '#95a5a6')
        return format_html(
            '<span style="background-color: {}; color: white; padding: 3px 10px; border-radius: 12px; font-size: 11px; font-weight: bold;">{}</span>',
            color, obj.get_category_display()
        )
    category_badge.short_description = 'Category'
    category_badge.admin_order_field = 'category'
    
    def subject_info(self, obj):
        """Display subject with code and scheme"""
        if obj.subject:
            return format_html(
                '<strong>{}</strong><br><small style="color: #666;">{} | Sem {} | {}</small>',
                obj.subject.name,
                obj.subject.code,
                obj.subject.semester,
                obj.subject.get_department_display()
            )
        return '—'
    subject_info.short_description = 'Subject Details'
    subject_info.admin_order_field = 'subject__name'
    
    def module_badge(self, obj):
        """Display module number as a badge"""
        return format_html(
            '<span style="background-color: #34495e; color: white; padding: 5px 12px; border-radius: 50%; font-weight: bold;">M{}</span>',
            obj.module_number
        )
    module_badge.short_description = 'Module'
    module_badge.admin_order_field = 'module_number'
    
    def approval_status(self, obj):
        """Display approval status with icon"""
        if obj.is_approved:
            return format_html(
                '<span style="color: #27ae60; font-weight: bold;">✓ Approved</span><br>'
                '<small style="color: #666;">by {}</small>',
                obj.approved_by.username if obj.approved_by else 'System'
            )
        return format_html('<span style="color: #e74c3c; font-weight: bold;">⏳ Pending</span>')
    approval_status.short_description = 'Status'
    approval_status.admin_order_field = 'is_approved'
    
    def stats_display(self, obj):
        """Display download and like statistics"""
        return format_html(
            '<span title="Downloads">📥 {}</span><br>'
            '<span title="Likes">❤️ {}</span>',
            obj.download_count,
            obj.like_count
        )
    stats_display.short_description = 'Engagement'
    
    def file_preview(self, obj):
        """Display file information with preview link"""
        if obj.file:
            try:
                file_url = obj.file_url
                download_url = obj.get_download_url()
                file_size_mb = obj.file_size / (1024 * 1024) if obj.file_size else 0
                
                return format_html(
                    '<div style="padding: 10px; background: #f8f9fa; border-radius: 5px;">'
                    '<p><strong>File:</strong> {}</p>'
                    '<p><strong>Size:</strong> {:.2f} MB</p>'
                    '<p><a href="{}" target="_blank" class="button" style="background-color: #3498db; color: white; padding: 8px 15px; text-decoration: none; border-radius: 4px; display: inline-block; margin-right: 10px;">👁️ View File</a>'
                    '<a href="{}" download class="button" style="background-color: #27ae60; color: white; padding: 8px 15px; text-decoration: none; border-radius: 4px; display: inline-block;">📥 Download</a></p>'
                    '</div>',
                    obj.file.name.split('/')[-1],
                    file_size_mb,
                    file_url or '#',
                    download_url or file_url or '#'
                )
            except Exception as e:
                return format_html('<p style="color: red;">Error loading file: {}</p>', str(e))
        return format_html('<p style="color: #999;">No file uploaded</p>')
    file_preview.short_description = 'File Preview'
    
    def changelist_view(self, request, extra_context=None):
        """Add extra context to changelist view"""
        extra_context = extra_context or {}
        extra_context['departments'] = json.dumps([
            {'value': code, 'label': name} for code, name in DEPARTMENT_CHOICES
        ])
        extra_context['semesters'] = json.dumps([
            {'value': i, 'label': f'Semester {i}'} for i in range(1, 9)
        ])
        extra_context['unapproved_count'] = AcademicResource.objects.filter(
            is_approved=False, is_active=True
        ).count()
        return super().changelist_view(request, extra_context)
    
    def get_urls(self):
        """Add custom URLs for bulk upload and bulk approve"""
        urls = super().get_urls()
        custom_urls = [
            path('bulk-upload/', self.admin_site.admin_view(self.bulk_upload_view), name='academics_bulk_upload'),
            path('bulk-approve/', self.admin_site.admin_view(self.bulk_approve_view), name='academics_bulk_approve'),
        ]
        return custom_urls + urls
    
    def bulk_upload_view(self, request):
        """Handle bulk PDF upload"""
        if request.method == 'POST':
            return self._process_bulk_upload(request)
        
        # GET request - show form
        schemes = Scheme.objects.filter(is_active=True).order_by('-year')
        
        # Prepare departments and semesters for the form
        departments = [{'value': code, 'label': name} for code, name in DEPARTMENT_CHOICES]
        semesters = [{'value': i, 'label': f'Semester {i}'} for i in range(1, 9)]
        
        # Get all subjects for initial population (will be filtered client-side)
        all_subjects = Subject.objects.filter(is_active=True).select_related('scheme').order_by('scheme__year', 'semester', 'code')
        subjects_data = [
            {
                'id': subj.id,
                'code': subj.code,
                'name': subj.name,
                'scheme_id': subj.scheme.id,
                'department': subj.department,
                'semester': subj.semester,
                'display': f"{subj.code} - {subj.name}"
            }
            for subj in all_subjects
        ]
        
        context = {
            'title': 'Bulk Upload Academic Resources',
            'schemes': schemes,
            'departments': json.dumps(departments),
            'semesters': json.dumps(semesters),
            'all_subjects': json.dumps(subjects_data),
            'site_header': self.admin_site.site_header,
            'site_title': self.admin_site.site_title,
            'has_permission': True,
        }
        
        return render(request, 'admin/academics/bulk_upload.html', context)
    
    @transaction.atomic
    def _process_bulk_upload(self, request):
        """Process bulk upload POST request"""
        try:
            subject_id = request.POST.get('subject')
            file_count = int(request.POST.get('file_count', 0))
            
            if not subject_id or file_count == 0:
                messages.error(request, 'Please select a subject and upload at least one file.')
                return redirect('admin:academics_bulk_upload')
            
            subject = Subject.objects.get(id=subject_id)
            uploaded_count = 0
            
            for i in range(file_count):
                file = request.FILES.get(f'file_{i}')
                title = request.POST.get(f'title_{i}')
                description = request.POST.get(f'description_{i}', '')
                category = request.POST.get(f'category_{i}', 'notes')
                module_number = int(request.POST.get(f'module_number_{i}', 1))
                pre_approve = request.POST.get(f'pre_approve_{i}') == 'true'
                
                if file and title:
                    resource = AcademicResource(
                        title=title,
                        description=description,
                        category=category,
                        subject=subject,
                        file=file,
                        module_number=module_number,
                        uploaded_by=request.user,
                        is_approved=pre_approve,
                        is_active=True
                    )
                    
                    if pre_approve:
                        resource.approved_by = request.user
                    
                    resource.save()
                    uploaded_count += 1
            
            messages.success(request, f'Successfully uploaded {uploaded_count} resource(s)!')
            return redirect('admin:academics_academicresource_changelist')
            
        except Exception as e:
            messages.error(request, f'Error during upload: {str(e)}')
            return redirect('admin:academics_bulk_upload')
    
    def bulk_approve_view(self, request):
        """Handle bulk approve/reject from dashboard"""
        if request.method == 'POST':
            action = request.POST.get('action')
            
            # Handle individual approve/reject
            if action and action.startswith('approve_'):
                resource_id = action.split('_')[1]
                try:
                    resource = AcademicResource.objects.get(id=resource_id)
                    resource.is_approved = True
                    resource.approved_by = request.user
                    resource.save()
                    messages.success(request, f'Approved: {resource.title}')
                except AcademicResource.DoesNotExist:
                    messages.error(request, 'Resource not found.')
            
            elif action and action.startswith('reject_'):
                resource_id = action.split('_')[1]
                try:
                    resource = AcademicResource.objects.get(id=resource_id)
                    resource.is_active = False
                    resource.save()
                    messages.success(request, f'Rejected: {resource.title}')
                except AcademicResource.DoesNotExist:
                    messages.error(request, 'Resource not found.')
            
            # Handle bulk approve/reject
            elif action == 'bulk_approve':
                resource_ids = request.POST.getlist('resource_ids')
                count = AcademicResource.objects.filter(id__in=resource_ids).update(
                    is_approved=True,
                    approved_by=request.user
                )
                messages.success(request, f'Approved {count} resource(s)!')
            
            elif action == 'bulk_reject':
                resource_ids = request.POST.getlist('resource_ids')
                count = AcademicResource.objects.filter(id__in=resource_ids).update(
                    is_active=False
                )
                messages.success(request, f'Rejected {count} resource(s)!')
        
        return redirect('admin:app_list', app_label='academics')
    
    def approve_resources(self, request, queryset):
        """Admin action to approve selected resources"""
        count = queryset.update(is_approved=True, approved_by=request.user)
        self.message_user(request, f'✓ {count} resource(s) approved successfully!', level='success')
    approve_resources.short_description = "✅ Approve selected resources"
    
    def reject_resources(self, request, queryset):
        """Admin action to reject selected resources"""
        count = queryset.update(is_active=False)
        self.message_user(request, f'✓ {count} resource(s) rejected successfully!', level='warning')
    reject_resources.short_description = "❌ Reject selected resources"
    
    def activate_resources(self, request, queryset):
        """Admin action to activate selected resources"""
        count = queryset.update(is_active=True)
        self.message_user(request, f'✓ {count} resource(s) activated successfully!', level='success')
    activate_resources.short_description = "🟢 Activate selected resources"
    
    def deactivate_resources(self, request, queryset):
        """Admin action to deactivate selected resources"""
        count = queryset.update(is_active=False)
        self.message_user(request, f'✓ {count} resource(s) deactivated successfully!', level='warning')
    deactivate_resources.short_description = "🔴 Deactivate selected resources"

    def file_link(self, obj):
        """Display clickable link to the file with Cloudinary URL"""
        if obj.file:
            try:
                file_url = obj.file_url
                download_url = obj.get_download_url()
                
                if file_url and file_url.startswith('http'):
                    return format_html(
                        '<a href="{}" target="_blank">View File</a> '
                        '(<a href="{}" download>Download</a>)<br>'
                        '<small style="color: #666;">{}</small>',
                        file_url, download_url or file_url, file_url
                    )
                elif file_url:
                    return format_html('<small style="color: #666;">{}</small>', file_url)
                else:
                    return format_html('<small style="color: #999;">File available but URL temporarily unavailable</small>')
            except Exception as e:
                return format_html('<small style="color: #f00;">Error loading file URL: {}</small>', str(e)[:50])
        return "No file uploaded"
    file_link.short_description = "File"

    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.uploaded_by = request.user
        if 'is_approved' in form.changed_data and obj.is_approved:
            obj.approved_by = request.user
        super().save_model(request, obj, form, change)


# AcademicCategory is not registered in admin, so it will not appear in the admin panel.
