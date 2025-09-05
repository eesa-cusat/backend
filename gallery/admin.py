from django.contrib import admin
from .models import Album, Photo


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    """Admin interface for Gallery Albums"""
    
    list_display = ['name', 'type', 'event_title', 'photo_count', 'created_at', 'created_by']
    list_filter = ['type', 'created_at']
    search_fields = ['name', 'description', 'event__title']
    readonly_fields = ['photo_count', 'created_at', 'created_by']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'type', 'description', 'cover_image')
        }),
        ('Event Link', {
            'fields': ('event',),
            'description': 'Link to event (required for EESA albums, must be empty for General albums)'
        }),
        ('Metadata', {
            'fields': ('photo_count', 'created_at', 'created_by'),
            'classes': ('collapse',)
        }),
    )
    
    def event_title(self, obj):
        return obj.event.title if obj.event else 'No Event'
    event_title.short_description = 'Event'
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set on creation
            obj.created_by = request.user
        super().save_model(request, obj, form, change)


@admin.register(Photo)
class PhotoAdmin(admin.ModelAdmin):
    """Admin interface for Gallery Photos"""
    
    list_display = ['__str__', 'album', 'uploaded_at', 'uploaded_by']
    list_filter = ['album', 'uploaded_at']
    search_fields = ['caption', 'album__name']
    readonly_fields = ['uploaded_at', 'uploaded_by']
    
    fieldsets = (
        ('Photo Details', {
            'fields': ('album', 'image', 'caption')
        }),
        ('Metadata', {
            'fields': ('uploaded_at', 'uploaded_by'),
            'classes': ('collapse',)
        }),
    )
    
    def save_model(self, request, obj, form, change):
        if not change:  # Only set on creation
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)
