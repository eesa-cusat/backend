from django.contrib import admin
from django.utils.html import format_html
from .models import GalleryCategory, GalleryImage, GalleryAlbum


@admin.register(GalleryCategory)
class GalleryCategoryAdmin(admin.ModelAdmin):
    list_display = ['name', 'category_type', 'album_count', 'total_images', 'is_active', 'display_order', 'created_at']
    list_filter = ['category_type', 'is_active', 'created_at']
    search_fields = ['name', 'description']
    readonly_fields = ['created_at', 'updated_at', 'album_count', 'total_images']
    list_editable = ['is_active', 'display_order']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'category_type', 'description', 'slug')
        }),
        ('Display Settings', {
            'fields': ('icon', 'is_active', 'display_order')
        }),
        ('Statistics', {
            'fields': ('album_count', 'total_images'),
            'classes': ('collapse',)
        }),
        ('Metadata', {
            'fields': ('created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def album_count(self, obj):
        return obj.album_count
    album_count.short_description = 'Albums'
    
    def total_images(self, obj):
        return obj.total_images
    total_images.short_description = 'Total Images'


@admin.register(GalleryAlbum)
class GalleryAlbumAdmin(admin.ModelAdmin):
    list_display = ['name', 'category', 'image_count', 'event_date', 'is_featured', 'is_public', 'is_active', 'created_by', 'created_at']
    list_filter = ['category', 'is_featured', 'is_public', 'is_active', 'event_date', 'created_by', 'created_at']
    search_fields = ['name', 'description', 'location']
    prepopulated_fields = {'slug': ('name',)}
    readonly_fields = ['created_by', 'created_at', 'updated_at', 'image_count']
    list_editable = ['is_featured', 'is_public', 'is_active']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'slug', 'description', 'category', 'cover_image')
        }),
        ('Event Details', {
            'fields': ('event_date', 'location')
        }),
        ('Settings', {
            'fields': ('is_active', 'is_public', 'is_featured', 'display_order')
        }),
        ('Statistics', {
            'fields': ('image_count',),
            'classes': ('collapse',)
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
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            # Allow admin and tech_head to manage all albums
            if hasattr(request.user, 'role') and request.user.role in ['admin', 'tech_head']:
                return qs
            # Regular users can only see their own albums
            return qs.filter(created_by=request.user)
        return qs


@admin.register(GalleryImage)
class GalleryImageAdmin(admin.ModelAdmin):
    list_display = ['title', 'image_preview', 'album', 'category', 'is_featured', 'is_public', 'uploaded_by', 'created_at']
    list_filter = ['album__category', 'album', 'is_featured', 'is_public', 'uploaded_by', 'created_at']
    search_fields = ['title', 'description', 'album__name', 'tags', 'photographer']
    readonly_fields = ['uploaded_by', 'file_size', 'image_width', 'image_height', 'created_at', 'updated_at', 'image_preview_large']
    list_editable = ['is_featured', 'is_public']
    date_hierarchy = 'created_at'
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('title', 'description', 'image', 'image_preview_large')
        }),
        ('Organization', {
            'fields': ('album', 'tags')
        }),
        ('Image Details', {
            'fields': ('photographer', 'camera_info', 'file_size', 'image_width', 'image_height')
        }),
        ('Display Settings', {
            'fields': ('is_featured', 'is_public', 'display_order')
        }),
        ('Metadata', {
            'fields': ('uploaded_by', 'created_at', 'updated_at'),
            'classes': ('collapse',)
        })
    )
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="width: 50px; height: 50px; object-fit: cover; border-radius: 4px;" />', obj.image.url)
        return "No Image"
    image_preview.short_description = 'Preview'
    
    def image_preview_large(self, obj):
        if obj.image:
            return format_html('<img src="{}" style="max-width: 300px; max-height: 300px; object-fit: contain;" />', obj.image.url)
        return "No Image"
    image_preview_large.short_description = 'Image Preview'
    
    def category(self, obj):
        return obj.album.category.name
    category.short_description = 'Category'
    
    def save_model(self, request, obj, form, change):
        if not change:  # If creating new object
            obj.uploaded_by = request.user
        super().save_model(request, obj, form, change)
    
    def get_queryset(self, request):
        qs = super().get_queryset(request)
        if not request.user.is_superuser:
            # Allow admin and tech_head to manage all images
            if hasattr(request.user, 'role') and request.user.role in ['admin', 'tech_head']:
                return qs
            # Regular users can only see their own uploads
            return qs.filter(uploaded_by=request.user)
        return qs
