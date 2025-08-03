from django.contrib import admin
from django.utils.html import format_html
from django.urls import reverse
from django.utils.safestring import mark_safe
from django.http import HttpResponse
from django.db.models import Count, Sum, Q
from django.utils import timezone

import csv
from .models import Event, EventRegistration, EventSpeaker, EventSchedule, Notification, NotificationSettings


class EventScheduleInline(admin.TabularInline):
    model = EventSchedule
    extra = 1
    fields = ['title', 'description', 'speaker', 'start_time', 'end_time', 'venue_details']


class EventSpeakerInline(admin.TabularInline):
    model = EventSpeaker
    extra = 1
    fields = ['name', 'title', 'organization', 'talk_title', 'order']
    readonly_fields = ['profile_image_preview']
    
    def profile_image_preview(self, obj):
        if obj.profile_image:
            return format_html('<img src="{}" style="width: 50px; height: 50px; border-radius: 50%;" />', obj.profile_image.url)
        return "No Image"
    profile_image_preview.short_description = "Profile Image"


@admin.register(Event)
class EventAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'event_type', 'start_date_formatted', 'status', 'registration_count',
        'is_upcoming_indicator', 'is_featured_indicator', 'created_by'
    ]
    list_filter = [
        'event_type', 'status', 'is_featured', 'is_active', 'start_date', 'registration_required',
        'payment_required', 'created_by'
    ]
    search_fields = ['title', 'description', 'location', 'venue']
    readonly_fields = ['created_by', 'created_at', 'updated_at', 'spots_remaining']
    inlines = [EventSpeakerInline, EventScheduleInline]
    actions = ['mark_as_featured', 'mark_as_published', 'mark_as_cancelled', 'export_registrations_csv']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'event_type', 'status')
        }),
        ('Schedule', {
            'fields': ('start_date', 'end_date', 'registration_deadline')
        }),
        ('Location', {
            'fields': ('location', 'venue', 'address', 'is_online', 'meeting_link')
        }),
        ('Registration Settings', {
            'fields': ('registration_required', 'max_participants', 'spots_remaining')
        }),
        ('Payment Settings', {
            'fields': ('registration_fee', 'payment_required', 'payment_qr_code', 'payment_upi_id', 'payment_instructions')
        }),
        ('Contact Information', {
            'fields': ('contact_person', 'contact_email', 'contact_phone')
        }),
        ('Media', {
            'fields': ('banner_image', 'event_flyer')
        }),
        ('Settings', {
            'fields': ('is_active', 'is_featured')
        }),
        ('Metadata', {
            'fields': ('created_by', 'created_at', 'updated_at'),
            'classes': ['collapse']
        })
    )
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by').annotate(
            registration_count_annotation=Count('registrations')
        )
    
    def start_date_formatted(self, obj):
        return obj.start_date.strftime('%Y-%m-%d %H:%M')
    start_date_formatted.short_description = 'Start Date'
    start_date_formatted.admin_order_field = 'start_date'
    
    def is_upcoming_indicator(self, obj):
        if obj.is_upcoming:
            return format_html('<span style="color: green;">⏰ Upcoming</span>')
        elif obj.is_ongoing:
            return format_html('<span style="color: blue;">🔴 Live</span>')
        else:
            return format_html('<span style="color: gray;">✅ Past</span>')
    is_upcoming_indicator.short_description = 'Status'
    
    def is_featured_indicator(self, obj):
        if obj.is_featured:
            return format_html('<span style="color: gold;">⭐ Featured</span>')
        return '—'
    is_featured_indicator.short_description = 'Featured'
    
    def registration_count(self, obj):
        # Use annotation if available, otherwise use model property
        count = getattr(obj, 'registration_count_annotation', None)
        if count is None:
            count = obj.registration_count
        
        if obj.max_participants:
            return f"{count}/{obj.max_participants}"
        return str(count)
    registration_count.short_description = 'Registrations'
    
    def mark_as_featured(self, request, queryset):
        queryset.update(is_featured=True)
        self.message_user(request, f'{queryset.count()} events marked as featured.')
    mark_as_featured.short_description = 'Mark selected events as featured'
    
    def mark_as_published(self, request, queryset):
        queryset.update(status='published')
        self.message_user(request, f'{queryset.count()} events published.')
    mark_as_published.short_description = 'Publish selected events'
    
    def mark_as_cancelled(self, request, queryset):
        queryset.update(status='cancelled')
        self.message_user(request, f'{queryset.count()} events cancelled.')
    mark_as_cancelled.short_description = 'Cancel selected events'
    
    def export_registrations_csv(self, request, queryset):
        """Export registrations for selected events to CSV"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="event_registrations.csv"'
        
        writer = csv.writer(response)
        writer.writerow([
            'Event Title', 'Name', 'Email', 'Mobile', 'Institution', 'Department',
            'Year of Study', 'Organization', 'Designation', 'Payment Status',
            'Payment Amount', 'Payment Date', 'Attended', 'Certificate Issued',
            'Registered Date'
        ])
        
        for event in queryset:
            for registration in event.registrations.all():
                writer.writerow([
                    event.title,
                    registration.name,
                    registration.email,
                    registration.mobile_number,
                    registration.institution or '',
                    registration.department or '',
                    registration.year_of_study or '',
                    registration.organization or '',
                    registration.designation or '',
                    registration.get_payment_status_display(),
                    float(registration.payment_amount) if registration.payment_amount else 0,
                    registration.payment_date.strftime('%Y-%m-%d %H:%M') if registration.payment_date else '',
                    'Yes' if registration.attended else 'No',
                    'Yes' if registration.certificate_issued else 'No',
                    registration.registered_at.strftime('%Y-%m-%d %H:%M')
                ])
        
        return response
    
    export_registrations_csv.short_description = 'Export registrations to CSV'
    
    def save_model(self, request, obj, form, change):
        """Auto-populate created_by field"""
        if not change:  # If creating new object
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(EventRegistration)
class EventRegistrationAdmin(admin.ModelAdmin):
    list_display = [
        'name', 'email', 'event', 'payment_status', 'payment_amount',
        'attended', 'certificate_issued', 'registered_at'
    ]
    list_filter = [
        'event', 'payment_status', 'attended', 'certificate_issued',
        'registered_at', 'institution', 'department'
    ]
    search_fields = ['name', 'email', 'mobile_number', 'institution', 'organization']
    readonly_fields = ['registered_at', 'updated_at']
    actions = ['mark_as_attended', 'mark_certificates_issued', 'verify_payment']
    
    fieldsets = (
        ('Event Registration', {
            'fields': ('event', 'registered_at')
        }),
        ('Personal Information', {
            'fields': ('name', 'email', 'mobile_number')
        }),
        ('Academic Information', {
            'fields': ('institution', 'department', 'year_of_study')
        }),
        ('Professional Information', {
            'fields': ('organization', 'designation')
        }),
        ('Payment Information', {
            'fields': (
                'payment_status', 'payment_amount', 'payment_verified_by',
                'payment_date', 'payment_reference'
            )
        }),
        ('Additional Information', {
            'fields': ('dietary_requirements', 'special_needs')
        }),
        ('Attendance & Certificates', {
            'fields': ('attended', 'certificate_issued')
        }),
        ('Metadata', {
            'fields': ('updated_at',),
            'classes': ['collapse']
        })
    )
    
    def mark_as_attended(self, request, queryset):
        queryset.update(attended=True)
        self.message_user(request, f'{queryset.count()} registrations marked as attended.')
    mark_as_attended.short_description = 'Mark as attended'
    
    def mark_certificates_issued(self, request, queryset):
        queryset.update(certificate_issued=True)
        self.message_user(request, f'{queryset.count()} certificates marked as issued.')
    mark_certificates_issued.short_description = 'Mark certificates as issued'
    
    def verify_payment(self, request, queryset):
        queryset.update(payment_status='paid', payment_verified_by=request.user, payment_date=timezone.now())
        self.message_user(request, f'{queryset.count()} payments verified.')
    verify_payment.short_description = 'Verify payment'


# EventSpeaker and EventSchedule removed from admin - managed through Event inlines only


# EventFeedback removed from admin - feedback managed through event interface


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = [
        'title', 'notification_type', 'priority', 'is_active', 
        'is_marquee', 'start_date', 'end_date', 'view_count', 'click_count'
    ]
    list_filter = [
        'notification_type', 'priority', 'is_active', 'is_marquee', 
        'start_date', 'created_at'
    ]
    search_fields = ['title', 'message']
    list_editable = ['is_active', 'is_marquee', 'priority']
    readonly_fields = ['view_count', 'click_count', 'created_at', 'updated_at']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Content', {
            'fields': ('title', 'message', 'notification_type', 'priority')
        }),
        ('Display Settings', {
            'fields': ('is_active', 'is_marquee', 'display_duration')
        }),
        ('Scheduling', {
            'fields': ('start_date', 'end_date'),
            'description': 'Control when the notification is shown'
        }),
        ('Actions', {
            'fields': ('action_url', 'action_text'),
            'classes': ('collapse',)
        }),
        ('Styling', {
            'fields': ('background_color', 'text_color'),
            'classes': ('collapse',)
        }),
        ('Analytics', {
            'fields': ('view_count', 'click_count'),
            'classes': ('collapse',)
        }),
        ('Meta', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new notification
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        return super().get_queryset(request).select_related('created_by')
    
    actions = ['mark_as_active', 'mark_as_inactive', 'mark_for_marquee', 'remove_from_marquee']
    
    def mark_as_active(self, request, queryset):
        queryset.update(is_active=True)
        self.message_user(request, f'{queryset.count()} notifications marked as active.')
    mark_as_active.short_description = 'Mark as active'
    
    def mark_as_inactive(self, request, queryset):
        queryset.update(is_active=False)
        self.message_user(request, f'{queryset.count()} notifications marked as inactive.')
    mark_as_inactive.short_description = 'Mark as inactive'
    
    def mark_for_marquee(self, request, queryset):
        queryset.update(is_marquee=True)
        self.message_user(request, f'{queryset.count()} notifications added to marquee.')
    mark_for_marquee.short_description = 'Add to marquee'
    
    def remove_from_marquee(self, request, queryset):
        queryset.update(is_marquee=False)
        self.message_user(request, f'{queryset.count()} notifications removed from marquee.')
    remove_from_marquee.short_description = 'Remove from marquee'


@admin.register(NotificationSettings)
class NotificationSettingsAdmin(admin.ModelAdmin):
    list_display = ['__str__', 'marquee_speed', 'max_notifications_display', 'auto_refresh_interval', 'updated_at']
    readonly_fields = ['updated_at']
    
    fieldsets = (
        ('Marquee Settings', {
            'fields': ('marquee_speed', 'marquee_pause_on_hover', 'max_notifications_display')
        }),
        ('Display Settings', {
            'fields': ('show_date', 'show_type_icon', 'enable_sound')
        }),
        ('Auto-refresh', {
            'fields': ('auto_refresh_interval',)
        }),
        ('Meta', {
            'fields': ('updated_at',),
            'classes': ('collapse',)
        })
    )
    
    def save_model(self, request, obj, form, change):
        obj.updated_by = request.user
        super().save_model(request, obj, form, change)
    
    def has_add_permission(self, request):
        # Only allow one settings instance
        return not NotificationSettings.objects.exists()
    
    def has_delete_permission(self, request, obj=None):
        # Don't allow deletion of settings
        return False
