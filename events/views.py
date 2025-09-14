from rest_framework import permissions, status, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone
from django.db.models import Prefetch
from django.core.cache import cache
from django.views.decorators.cache import cache_page
from .models import Event, EventRegistration, EventSpeaker, EventSchedule, EventFeedback
from .serializers import (
    EventSerializer, EventListSerializer, EventRegistrationSerializer,
    EventSpeakerSerializer, EventScheduleSerializer, EventFeedbackSerializer
)
from accounts.permissions import IsEventsTeamOrReadOnly


class EventPageNumberPagination(PageNumberPagination):
    """Custom pagination for events"""
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 50


class EventViewSet(viewsets.ModelViewSet):
    """Event management with pagination and optimization"""
    serializer_class = EventSerializer
    permission_classes = [IsEventsTeamOrReadOnly]
    pagination_class = EventPageNumberPagination
    
    def get_serializer_class(self):
        if self.action == 'list':
            return EventListSerializer
        return EventSerializer
    
    def get_queryset(self):
        # Optimized queryset with select_related and prefetch_related
        queryset = Event.objects.select_related('created_by').prefetch_related(
            Prefetch('registrations', queryset=EventRegistration.objects.only('id', 'email')),
            'speakers',
            'album'  # Add album prefetch for gallery backlinks
        ).only(
            'id', 'title', 'description', 'event_type', 'status', 'start_date', 
            'end_date', 'location', 'venue', 'registration_required', 
            'max_participants', 'banner_image', 'is_featured', 'created_at',
            'created_by__username', 'created_by__first_name', 'created_by__last_name'
        )
        
        # Public users can only see published events
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(status='published', is_active=True)
        
        # Basic filters
        event_type = self.request.query_params.get('event_type')
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        
        featured_only = self.request.query_params.get('featured')
        if featured_only and featured_only.lower() == 'true':
            queryset = queryset.filter(is_featured=True)
        
        upcoming_only = self.request.query_params.get('upcoming')
        if upcoming_only and upcoming_only.lower() == 'true':
            queryset = queryset.filter(start_date__gt=timezone.now())
        
        return queryset.order_by('-start_date')
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['post'])
    def register(self, request, pk=None):
        """Register for an event"""
        event = self.get_object()
        
        if not event.is_registration_open:
            return Response(
                {'error': 'Registration is closed for this event'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        email = request.data.get('email')
        if email and EventRegistration.objects.filter(event=event, email=email).exists():
            return Response(
                {'error': 'Already registered for this event'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        serializer = EventRegistrationSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(event=event)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


class EventRegistrationViewSet(viewsets.ModelViewSet):
    """Event registration management"""
    queryset = EventRegistration.objects.all()
    serializer_class = EventRegistrationSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    
    def get_permissions(self):
        """Allow anyone to register, but only staff to view all"""
        if self.action == 'create':
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]


class EventSpeakerViewSet(viewsets.ModelViewSet):
    """Event speaker management"""
    queryset = EventSpeaker.objects.all()
    serializer_class = EventSpeakerSerializer
    permission_classes = [IsEventsTeamOrReadOnly]


class EventScheduleViewSet(viewsets.ModelViewSet):
    """Event schedule management"""
    queryset = EventSchedule.objects.all()
    serializer_class = EventScheduleSerializer
    permission_classes = [IsEventsTeamOrReadOnly]


class EventFeedbackViewSet(viewsets.ModelViewSet):
    """Event feedback management"""
    queryset = EventFeedback.objects.all()
    serializer_class = EventFeedbackSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def upcoming_events(request):
    """Get upcoming events"""
    events = Event.objects.filter(
        status='published',
        is_active=True,
        start_date__gt=timezone.now()
    ).order_by('start_date')[:5]
    
    serializer = EventListSerializer(events, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def featured_events(request):
    """Get featured events with caching"""
    cache_key = 'featured_events_list'
    cached_data = cache.get(cache_key)
    
    if cached_data is None:
        events = Event.objects.select_related('created_by').filter(
            status='published',
            is_active=True,
            is_featured=True
        ).prefetch_related('registrations').order_by('-start_date')[:3]
        
        serializer = EventListSerializer(events, many=True)
        cached_data = serializer.data
        cache.set(cache_key, cached_data, 300)  # Cache for 5 minutes
    
    return Response(cached_data)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def event_stats(request):
    """Get event statistics"""
    stats = {
        'total_events': Event.objects.count(),
        'published_events': Event.objects.filter(status='published').count(),
        'upcoming_events': Event.objects.filter(
            status='published',
            start_date__gt=timezone.now()
        ).count(),
        'total_registrations': EventRegistration.objects.count()
    }
    return Response(stats)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def quick_register(request):
    """Quick registration for events without authentication"""
    event_id = request.data.get('event_id') or request.data.get('event')
    
    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        return Response(
            {'error': 'Event not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    if not event.is_registration_open:
        return Response(
            {'error': 'Registration is closed for this event'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    serializer = EventRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(event=event)
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def submit_feedback(request):
    """Submit feedback for an event"""
    serializer = EventFeedbackSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
