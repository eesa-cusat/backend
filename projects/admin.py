from django.contrib import admin
from django.utils.html import format_html
from .models import Project, TeamMember, ProjectImage, ProjectVideo



class TeamMemberInline(admin.TabularInline):
    """Inline admin for team members"""
    model = TeamMember
    extra = 1
    fields = ('name', 'role', 'linkedin_url')


class ProjectImageInline(admin.TabularInline):
    """Inline admin for project images"""
    model = ProjectImage
    extra = 1
    fields = ('image', 'caption', 'is_featured')
    readonly_fields = ('image_preview',)
    
    def image_preview(self, obj):
        if obj.image:
            return format_html('<img src="{}" width="100" height="100" style="border-radius: 5px;" />', obj.image.url)
        return "No image"
    image_preview.short_description = 'Preview'


class ProjectVideoInline(admin.TabularInline):
    """Inline admin for project videos"""
    model = ProjectVideo
    extra = 1
    fields = ('video_url', 'title', 'is_featured')


@admin.register(Project)
class ProjectAdmin(admin.ModelAdmin):
    """Project Administration - Create and Manage Projects"""
    
    list_display = ['title', 'category_display', 'student_batch', 'team_size', 'featured_status', 'published_status', 'created_by', 'created_at']
    list_filter = ['category', 'is_featured', 'is_published', 'created_by', 'student_batch']
    search_fields = ['title', 'description', 'abstract', 'student_batch']
    ordering = ['-is_featured', '-created_at']
    
    fieldsets = [
        ('Project Information', {
            'fields': ['title', 'description', 'abstract', 'category'],
            'classes': ['wide']
        }),
        ('Student Information', {
            'fields': ['student_batch'],
            'classes': ['wide']
        }),
        ('Project Files & Links', {
            'fields': ['project_report', 'project_images', 'github_url', 'demo_url'],
            'classes': ['wide']
        }),
        ('Project Settings', {
            'fields': ['is_featured', 'is_published'],
            'classes': ['wide']
        }),
        ('Management Info', {
            'fields': ['created_by', 'created_at', 'updated_at'],
            'classes': ['collapse']
        })
    ]
    
    readonly_fields = ['created_by', 'created_at', 'updated_at']
    inlines = [TeamMemberInline, ProjectImageInline, ProjectVideoInline]
    
    def save_model(self, request, obj, form, change):
        if not change:  # This is a new object being created
            obj.created_by = request.user
        super().save_model(request, obj, form, change)
    
    def category_display(self, obj):
        return obj.get_category_display()
    category_display.short_description = 'Category'
    
    def team_size(self, obj):
        total_members = obj.team_members.count()
        return format_html('<span style="color: blue; font-weight: bold;">{} member(s)</span>', total_members)
    team_size.short_description = 'Team Size'
    
    def featured_status(self, obj):
        if obj.is_featured:
            return format_html('<span style="color: green; font-weight: bold;">★ Featured</span>')
        return format_html('<span style="color: gray;">Not Featured</span>')
    featured_status.short_description = 'Featured'
    
    def published_status(self, obj):
        if obj.is_published:
            return format_html('<span style="color: green;">✓ Published</span>')
        return format_html('<span style="color: red;">✗ Draft</span>')
    published_status.short_description = 'Status'
    
    actions = ['make_featured', 'remove_featured', 'publish_projects', 'unpublish_projects']
    
    def make_featured(self, request, queryset):
        updated = queryset.update(is_featured=True)
        self.message_user(request, f'{updated} project(s) marked as featured')
    make_featured.short_description = 'Mark selected projects as featured'
    
    def remove_featured(self, request, queryset):
        updated = queryset.update(is_featured=False)
        self.message_user(request, f'{updated} project(s) removed from featured')
    remove_featured.short_description = 'Remove featured status'
    
    def publish_projects(self, request, queryset):
        updated = queryset.update(is_published=True)
        self.message_user(request, f'{updated} project(s) published')
    publish_projects.short_description = 'Publish selected projects'
    
    def unpublish_projects(self, request, queryset):
        updated = queryset.update(is_published=False)
        self.message_user(request, f'{updated} project(s) marked as draft')
    unpublish_projects.short_description = 'Mark selected projects as draft'


# Note: TeamMember, ProjectImage, and ProjectVideo are managed through Project admin inlines only
# This keeps the admin interface clean and shows only "Project Administration" with inline editing
