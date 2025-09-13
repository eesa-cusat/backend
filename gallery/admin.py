from django.contrib import admin
from django import forms
from .models import Album, Photo


class AlbumAdminForm(forms.ModelForm):
    """Custom form for Album admin with validation"""
    
    class Meta:
        model = Album
        fields = '__all__'
    
    def clean(self):
        cleaned_data = super().clean()
        album_type = cleaned_data.get('type')
        event = cleaned_data.get('event')
        batch_year = cleaned_data.get('batch_year')
        
        # Clear inappropriate fields based on album type to prevent FK constraint errors
        if album_type == 'general':
            cleaned_data['event'] = None
            cleaned_data['batch_year'] = None
        elif album_type == 'eesa':
            cleaned_data['batch_year'] = None
            if not event:
                raise forms.ValidationError("EESA albums must be linked to an event.")
        elif album_type == 'alumni':
            cleaned_data['event'] = None
            if not batch_year:
                raise forms.ValidationError("Alumni albums must have a batch year.")
        
        return cleaned_data
    
    def save(self, commit=True):
        instance = super().save(commit=False)
        
        # Ensure fields are properly cleared based on album type
        if instance.type == 'general':
            instance.event = None
            instance.batch_year = None
        elif instance.type == 'eesa':
            instance.batch_year = None
        elif instance.type == 'alumni':
            instance.event = None
            
        if commit:
            instance.save()
        return instance


@admin.register(Album)
class AlbumAdmin(admin.ModelAdmin):
    """Admin interface for Gallery Albums"""
    
    form = AlbumAdminForm
    list_display = ['name', 'type', 'event_title', 'batch_year', 'photo_count', 'created_at', 'created_by']
    list_filter = ['type', 'created_at', 'batch_year']
    search_fields = ['name', 'description', 'event__title']
    readonly_fields = ['photo_count', 'created_at', 'created_by']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'type', 'description', 'cover_image')
        }),
        ('Relations', {
            'fields': ('event', 'batch_year'),
            'description': 'Event (required for EESA albums) | Batch Year (required for Alumni albums) | Leave both empty for General albums'
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
        
    def get_form(self, request, obj=None, **kwargs):
        form = super().get_form(request, obj, **kwargs)
        
        # Make event field not required in the form (validation handled in clean())
        if 'event' in form.base_fields:
            form.base_fields['event'].required = False
        
        # Make batch_year field not required in the form (validation handled in clean())
        if 'batch_year' in form.base_fields:
            form.base_fields['batch_year'].required = False
            
        return form


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
