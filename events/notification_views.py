from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from rest_framework.response import Response
from rest_framework import status
from django.utils import timezone
from django.db.models import F, Q
from .models import Notification, NotificationSettings
from .serializers import NotificationSerializer, NotificationSettingsSerializer


@api_view(['GET'])
@permission_classes([AllowAny])
def active_notifications(request):
    """Get all currently active notifications"""
    now = timezone.now()
    
    notifications = Notification.objects.filter(
        is_active=True,
        start_date__lte=now
    ).filter(
        Q(end_date__isnull=True) | Q(end_date__gte=now)
    ).order_by('-priority', '-created_at')
    
    # Increment view count for all returned notifications
    notification_ids = list(notifications.values_list('id', flat=True))
    Notification.objects.filter(id__in=notification_ids).update(
        view_count=F('view_count') + 1
    )
    
    serializer = NotificationSerializer(notifications, many=True)
    return Response({
        'notifications': serializer.data,
        'count': notifications.count()
    })


@api_view(['GET'])
@permission_classes([AllowAny])
def marquee_notifications(request):
    """Get notifications for marquee display"""
    now = timezone.now()
    settings = NotificationSettings.get_settings()
    
    notifications = Notification.objects.filter(
        is_active=True,
        is_marquee=True,
        start_date__lte=now
    ).filter(
        Q(end_date__isnull=True) | Q(end_date__gte=now)
    ).order_by('-priority', '-created_at')
    
    # Limit to max display count from settings
    if settings:
        notifications = notifications[:settings.max_notifications_display]
    else:
        notifications = notifications[:5]  # Default limit
    
    # Increment view count for marquee notifications
    notification_ids = list(notifications.values_list('id', flat=True))
    Notification.objects.filter(id__in=notification_ids).update(
        view_count=F('view_count') + 1
    )
    
    serializer = NotificationSerializer(notifications, many=True)
    return Response({
        'notifications': serializer.data,
        'count': notifications.count(),
        'settings': NotificationSettingsSerializer(settings).data if settings else None
    })


@api_view(['POST'])
@permission_classes([AllowAny])
def notification_clicked(request, pk):
    """Track notification click"""
    try:
        notification = Notification.objects.get(pk=pk, is_active=True)
        notification.increment_click_count()
        
        return Response({
            'message': 'Click tracked successfully',
            'click_count': notification.click_count
        })
    except Notification.DoesNotExist:
        return Response(
            {'error': 'Notification not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )


@api_view(['GET'])
@permission_classes([AllowAny])
def notification_settings(request):
    """Get notification system settings"""
    settings = NotificationSettings.get_settings()
    
    if settings:
        serializer = NotificationSettingsSerializer(settings)
        return Response(serializer.data)
    else:
        # Return default settings if none exist
        return Response({
            'marquee_speed': 50,
            'marquee_pause_on_hover': True,
            'max_notifications_display': 5,
            'show_date': True,
            'show_type_icon': True,
            'enable_sound': False,
            'auto_refresh_interval': 30
        })


@api_view(['GET'])
@permission_classes([AllowAny])
def notifications_by_type(request, notification_type):
    """Get notifications by type"""
    now = timezone.now()
    
    notifications = Notification.objects.filter(
        is_active=True,
        notification_type=notification_type,
        start_date__lte=now
    ).filter(
        Q(end_date__isnull=True) | Q(end_date__gte=now)
    ).order_by('-priority', '-created_at')
    
    serializer = NotificationSerializer(notifications, many=True)
    return Response({
        'notifications': serializer.data,
        'type': notification_type,
        'count': notifications.count()
    })
