from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for viewsets
router = DefaultRouter()
router.register(r'events', views.EventViewSet, basename='event')
router.register(r'registrations', views.EventRegistrationViewSet, basename='eventregistration')
router.register(r'speakers', views.EventSpeakerViewSet, basename='eventspeaker')
router.register(r'schedules', views.EventScheduleViewSet, basename='eventschedule')
router.register(r'feedback', views.EventFeedbackViewSet, basename='eventfeedback')

urlpatterns = [
    # Include router URLs
    path('', include(router.urls)),
    
    # Additional utility endpoints
    path('upcoming/', views.upcoming_events, name='upcoming-events'),
    path('featured/', views.featured_events, name='featured-events'),
    path('stats/', views.event_stats, name='event-stats'),
    path('quick-register/', views.quick_register, name='quick-register'),
    path('submit-feedback/', views.submit_feedback, name='submit-feedback'),
]
