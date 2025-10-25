"""
Custom context processors for EESA Backend
"""
from django.contrib.admin.models import LogEntry


def recent_actions(request):
    """
    Add filtered recent actions to context:
    - Superusers see all actions
    - Regular users see only their own actions
    """
    if not request.user.is_authenticated:
        return {'recent_actions': []}
    
    if request.user.is_superuser:
        # Superusers see all recent actions
        actions = LogEntry.objects.select_related(
            'content_type', 'user'
        ).order_by('-action_time')[:15]
    else:
        # Regular users see only their own actions
        actions = LogEntry.objects.filter(
            user=request.user
        ).select_related(
            'content_type', 'user'
        ).order_by('-action_time')[:15]
    
    return {'filtered_recent_actions': actions}
