"""
Custom Admin Site Configuration
Filters recent actions based on user permissions
"""
from django.contrib import admin
from django.contrib.admin import AdminSite
from django.contrib.admin.models import LogEntry


class EESAAdminSite(AdminSite):
    """
    Custom Admin Site that filters recent actions:
    - Superusers see all actions (last 15)
    - Regular admins see only their own actions (last 15)
    """
    site_header = "⚡ EESA Administration Portal"
    site_title = "EESA Admin"
    index_title = "Welcome to EESA Admin Panel"
    
    def index(self, request, extra_context=None):
        """
        Override index to add filtered recent actions
        """
        extra_context = extra_context or {}
        
        # Filter recent actions based on user permissions
        if request.user.is_authenticated:
            if request.user.is_superuser:
                # Superusers see all recent actions
                recent_actions = LogEntry.objects.select_related(
                    'content_type', 'user'
                ).order_by('-action_time')[:15]
            else:
                # Regular admins see only their own actions
                recent_actions = LogEntry.objects.filter(
                    user=request.user
                ).select_related(
                    'content_type', 'user'
                ).order_by('-action_time')[:15]
            
            extra_context['admin_log'] = recent_actions
        
        return super().index(request, extra_context)


# Replace the default admin site with our custom one
admin.site = EESAAdminSite()
admin.site.site_header = "⚡ EESA Administration Portal"
admin.site.site_title = "EESA Admin"
admin.site.index_title = "Welcome to EESA Admin Panel"

