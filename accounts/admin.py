from django.contrib import admin
from django.contrib.auth.admin import UserAdmin
from django.utils.html import format_html
from .models import User, TeamMember


@admin.register(User)
class CustomUserAdmin(UserAdmin):
    list_display = ['username', 'email', 'first_name', 'last_name', 'is_staff', 'is_active', 'get_groups']
    list_filter = ['is_staff', 'is_active', 'date_joined', 'groups']
    search_fields = ['username', 'email', 'first_name', 'last_name']
    ordering = ['username']
    
    fieldsets = (
        (None, {'fields': ('username', 'password')}),
        ('Personal info', {'fields': ('first_name', 'last_name', 'email', 'mobile_number')}),
        ('Permissions', {
            'fields': ('is_active', 'is_staff', 'is_superuser', 'groups', 'user_permissions'),
            'description': 'Assign groups and individual permissions. Users with groups automatically become staff.'
        }),
        ('Important dates', {'fields': ('last_login', 'date_joined')}),
    )
    
    add_fieldsets = (
        (None, {
            'classes': ('wide',),
            'fields': ('username', 'email', 'password1', 'password2', 'is_staff', 'is_active'),
        }),
    )
    
    def get_groups(self, obj):
        """Show user groups"""
        groups = obj.groups.all()
        if groups:
            return ", ".join([group.name for group in groups])
        return "No groups"
    get_groups.short_description = 'Groups'


@admin.register(TeamMember)
class TeamMemberAdmin(admin.ModelAdmin):
    list_display = ['name', 'position', 'team_type', 'is_active', 'order']
    list_filter = ['team_type', 'is_active']
    search_fields = ['name', 'position', 'bio']
    list_editable = ['is_active', 'order']
    ordering = ['order', 'name']
    
    fieldsets = (
        ('Basic Information', {
            'fields': ('name', 'position', 'team_type', 'bio')
        }),
        ('Contact Information', {
            'fields': ('email', 'linkedin_url', 'github_url')
        }),
        ('Media', {
            'fields': ('image',)
        }),
        ('Display Settings', {
            'fields': ('is_active', 'order')
        }),
    )
