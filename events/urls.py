from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views
from . import notification_views

# Create router for viewsets
router = DefaultRouter()
router.register(r'', views.EventViewSet, basename='event')  # Main events endpoint at /api/events/
router.register(r'registrations', views.EventRegistrationViewSet, basename='eventregistration')
router.register(r'speakers', views.EventSpeakerViewSet, basename='eventspeaker')
router.register(r'schedules', views.EventScheduleViewSet, basename='eventschedule')
router.register(r'feedback', views.EventFeedbackViewSet, basename='eventfeedback')

urlpatterns = [
    # Additional utility endpoints FIRST (before router catches everything)
    path('upcoming/', views.upcoming_events, name='upcoming-events'),
    path('featured/', views.featured_events, name='featured-events'),
    path('stats/', views.event_stats, name='event-stats'),
    path('quick-register/', views.quick_register, name='quick-register'),
    path('submit-feedback/', views.submit_feedback, name='submit-feedback'),
    
    # Include router URLs (this catches remaining paths)
    path('', include(router.urls)),
    
    # Notification endpoints
    path('notifications/', notification_views.active_notifications, name='active-notifications'),
    path('notifications/marquee/', notification_views.marquee_notifications, name='marquee-notifications'),
    path('notifications/settings/', notification_views.notification_settings, name='notification-settings'),
    path('notifications/type/<str:notification_type>/', notification_views.notifications_by_type, name='notifications-by-type'),
    path('notifications/<int:pk>/click/', notification_views.notification_clicked, name='notification-clicked'),
]
