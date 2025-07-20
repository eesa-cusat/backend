from django.contrib import admin
from .models import Company, PlacementDrive, StudentCoordinator, PlacementStatistics, PlacedStudent, PlacementBrochure


@admin.register(Company)
class CompanyAdmin(admin.ModelAdmin):
    list_display = ['name', 'industry', 'location', 'is_verified', 'is_active', 'created_at']
    list_filter = ['industry', 'company_size', 'is_verified', 'is_active', 'created_at']
    search_fields = ['name', 'industry', 'location', 'contact_person']
    readonly_fields = ['created_by', 'created_at', 'updated_at']
    list_editable = ['is_verified', 'is_active']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'description', 'website', 'logo')
        }),
        ('Company Details', {
            'fields': ('industry', 'location', 'company_size')
        }),
        ('Contact Information', {
            'fields': ('contact_person', 'contact_email', 'contact_phone')
        }),
        ('Status', {
            'fields': ('is_active', 'is_verified')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        """Auto-populate created_by field"""
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(PlacementDrive)
class PlacementDriveAdmin(admin.ModelAdmin):
    list_display = ['title', 'company', 'job_type', 'package_lpa', 'drive_date', 'is_active', 'is_featured']
    list_filter = ['job_type', 'drive_mode', 'is_active', 'is_featured', 'drive_date', 'company']
    search_fields = ['title', 'company__name', 'description']
    readonly_fields = ['created_by', 'created_at', 'updated_at']
    list_editable = ['is_active', 'is_featured']
    date_hierarchy = 'drive_date'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('company', 'title', 'description', 'job_type')
        }),
        ('Requirements', {
            'fields': ('min_cgpa', 'min_percentage', 'eligible_batches')
        }),
        ('Package Details', {
            'fields': ('package_lpa', 'package_details')
        }),
        ('Important Dates', {
            'fields': ('registration_start', 'registration_end', 'drive_date', 'result_date'),
            'description': 'All dates are required for proper drive functionality'
        }),
        ('Application & Drive Details', {
            'fields': ('application_link', 'location', 'drive_mode', 'required_documents', 'additional_info')
        }),
        ('Status', {
            'fields': ('is_active', 'is_featured')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_readonly_fields(self, request, obj=None):
        """Make computed fields read-only"""
        readonly = list(self.readonly_fields)
        if obj:  # Editing existing object
            # Add computed fields to readonly when editing
            readonly.extend(['created_by'])
        return readonly


# PlacementApplication removed from admin - managed through PlacementDrive interface


@admin.register(StudentCoordinator)
class StudentCoordinatorAdmin(admin.ModelAdmin):
    list_display = ['user', 'designation', 'mobile_number', 'email', 'is_active', 'display_order']
    list_filter = ['is_active', 'designation']
    search_fields = ['user__username', 'user__first_name', 'user__last_name', 'mobile_number', 'email']
    readonly_fields = ['created_at', 'updated_at']
    list_editable = ['is_active', 'display_order']
    
    fieldsets = (
        ('User Information', {
            'fields': ('user', 'designation')
        }),
        ('Contact Details', {
            'fields': ('mobile_number', 'email', 'profile_picture')
        }),
        ('Additional Information', {
            'fields': ('bio',)
        }),
        ('Display Settings', {
            'fields': ('is_active', 'display_order')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Pre-populate email with user's email if creating new coordinator
        if not obj and 'user' in form.base_fields:
            form.base_fields['email'].help_text += " (Will auto-populate from selected user)"
        return form


@admin.register(PlacementStatistics)
class PlacementStatisticsAdmin(admin.ModelAdmin):
    list_display = ['batch_year', 'academic_year', 'total_students', 'total_placed', 'placement_percentage', 'average_package']
    list_filter = ['academic_year', 'batch_year']
    search_fields = ['academic_year', 'batch_year']
    readonly_fields = ['placement_percentage', 'created_at', 'updated_at']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('academic_year', 'batch_year')
        }),
        ('Student Statistics', {
            'fields': ('total_students', 'total_placed', 'placement_percentage')
        }),
        ('Package Statistics', {
            'fields': ('highest_package', 'average_package', 'median_package')
        }),
        ('Companies Statistics', {
            'fields': ('total_companies_visited', 'total_offers')
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        # Set default branch to EEE since it's a department website
        if 'branch' in form.base_fields and not obj:
            form.base_fields['branch'].initial = 'Electrical & Electronics Engineering'
        return form
    
    def save_model(self, request, obj, form, change):
        # Auto-set branch if not provided
        if not obj.branch:
            obj.branch = 'Electrical & Electronics Engineering'
        super().save_model(request, obj, form, change)


@admin.register(PlacedStudent)
class PlacedStudentAdmin(admin.ModelAdmin):
    list_display = ['student_name', 'company', 'job_title', 'package_lpa', 'batch_year', 'is_verified', 'offer_date']
    list_filter = ['batch_year', 'job_type', 'is_verified', 'company', 'offer_date']
    search_fields = ['student_name', 'student_email', 'roll_number', 'company__name', 'job_title']
    readonly_fields = ['created_by', 'created_at', 'updated_at']
    list_editable = ['is_verified']
    date_hierarchy = 'offer_date'
    
    fieldsets = (
        ('Student Information', {
            'fields': ('student_name', 'student_email', 'roll_number', 'batch_year', 'cgpa', 'student_photo')
        }),
        ('Placement Details', {
            'fields': ('company', 'placement_drive', 'job_title', 'package_lpa', 'package_details', 'work_location', 'job_type')
        }),
        ('Important Dates', {
            'fields': ('offer_date', 'joining_date')
        }),
        ('Documents & Testimonial', {
            'fields': ('offer_letter', 'testimonial')
        }),
        ('Status', {
            'fields': ('is_verified', 'is_active')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(PlacementBrochure)
class PlacementBrochureAdmin(admin.ModelAdmin):
    list_display = ['title', 'academic_year', 'is_current', 'uploaded_by', 'created_at']
    list_filter = ['academic_year', 'is_current', 'created_at']
    search_fields = ['title', 'description']
    readonly_fields = ['uploaded_by', 'created_at', 'updated_at']
    list_editable = ['is_current']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'academic_year')
        }),
        ('File Upload', {
            'fields': ('file',)
        }),
        ('Status', {
            'fields': ('is_current',)
        }),
        ('Metadata', {
            'fields': ('uploaded_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)
