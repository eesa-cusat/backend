from rest_framework import generics, permissions, status, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from django.db.models import Q, Count, Prefetch
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.core.cache import cache
from .models import Event, EventRegistration, EventSpeaker, EventSchedule, EventFeedback
from .serializers import (
    EventSerializer, EventListSerializer, EventRegistrationSerializer,
    EventRegistrationCreateSerializer, EventSpeakerSerializer, EventScheduleSerializer, EventFeedbackSerializer
)
from accounts.permissions import IsEventsTeamOrReadOnly


class EventViewSet(viewsets.ModelViewSet):
    """Comprehensive event management viewset"""
    
    queryset = Event.objects.all()
    serializer_class = EventSerializer
    permission_classes = [IsEventsTeamOrReadOnly]
    
    def get_serializer_class(self):
        """Use different serializers for different actions"""
        if self.action == 'list':
            return EventListSerializer
        return EventSerializer
    
    def get_queryset(self):
        """Filter events based on user permissions and query params with optimizations"""
        queryset = Event.objects.select_related('created_by').prefetch_related(
            Prefetch('registrations', queryset=EventRegistration.objects.only('id', 'email')),
            Prefetch('speakers', queryset=EventSpeaker.objects.only('id', 'name', 'designation')),
            'schedule'
        )
        
        # Public users can only see published and active events
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(status='published', is_active=True)
        
        # Filter by query parameters
        event_type = self.request.query_params.get('event_type')
        status_filter = self.request.query_params.get('status')
        featured_only = self.request.query_params.get('featured')
        upcoming_only = self.request.query_params.get('upcoming')
        
        if event_type:
            queryset = queryset.filter(event_type=event_type)
        
        if status_filter:
            queryset = queryset.filter(status=status_filter)
        
        if featured_only and featured_only.lower() == 'true':
            queryset = queryset.filter(is_featured=True)
        
        if upcoming_only and upcoming_only.lower() == 'true':
            queryset = queryset.filter(start_date__gt=timezone.now())
        
        return queryset.order_by('-start_date')
    
    def perform_create(self, serializer):
        """Set created_by to current user"""
        serializer.save(created_by=self.request.user)
    
    @action(detail=True, methods=['get'])
    def registrations(self, request, pk=None):
        """Get registrations for a specific event"""
        event = self.get_object()
        registrations = event.registrations.all()
        
        serializer = EventRegistrationSerializer(registrations, many=True)
        return Response({
            'registrations': serializer.data,
            'count': registrations.count(),
            'event': event.title
        })
    
    @action(detail=True, methods=['post'])
    def register(self, request, pk=None):
        """Register for an event"""
        event = self.get_object()
        
        # Check if registration is open
        if not event.is_registration_open:
            return Response(
                {'error': 'Registration is closed for this event'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Check if user already registered (by email)
        email = request.data.get('email')
        if email and EventRegistration.objects.filter(event=event, email=email).exists():
            return Response(
                {'error': 'You have already registered for this event'},
                status=status.HTTP_400_BAD_REQUEST
            )
        
        # Create registration
        serializer = EventRegistrationCreateSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(event=event)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    @action(detail=True, methods=['get'])
    def speakers(self, request, pk=None):
        """Get speakers for a specific event"""
        event = self.get_object()
        speakers = event.speakers.all()
        
        serializer = EventSpeakerSerializer(speakers, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def schedule(self, request, pk=None):
        """Get schedule for a specific event"""
        event = self.get_object()
        schedule = event.schedule.all()
        
        serializer = EventScheduleSerializer(schedule, many=True)
        return Response(serializer.data)
    
    @action(detail=True, methods=['get'])
    def feedback(self, request, pk=None):
        """Get feedback for a specific event"""
        event = self.get_object()
        feedback = event.feedback.all()
        
        serializer = EventFeedbackSerializer(feedback, many=True)
        return Response(serializer.data)


class EventRegistrationViewSet(viewsets.ModelViewSet):
    """Event registration management"""
    
    queryset = EventRegistration.objects.all()
    serializer_class = EventRegistrationSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """Allow anyone to register, but only staff to view all"""
        if self.action == 'create':
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filter registrations based on user permissions"""
        queryset = EventRegistration.objects.all()
        
        # Staff can see all registrations
        if self.request.user.is_authenticated and self.request.user.role in ['superuser', 'faculty_coordinator', 'tech_head']:
            return queryset
        
        # Regular users can only see their own registrations
        if self.request.user.is_authenticated:
            return queryset.filter(email=self.request.user.email)
        
        return queryset.none()
    
    @action(detail=True, methods=['post'])
    def mark_attended(self, request, pk=None):
        """Mark registration as attended (staff only)"""
        if not request.user.is_authenticated or request.user.role not in ['superuser', 'faculty_coordinator', 'tech_head']:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        registration = self.get_object()
        registration.attended = True
        registration.save()
        
        return Response({'message': 'Registration marked as attended'})
    
    @action(detail=True, methods=['post'])
    def issue_certificate(self, request, pk=None):
        """Issue certificate (staff only)"""
        if not request.user.is_authenticated or request.user.role not in ['superuser', 'faculty_coordinator', 'tech_head']:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        registration = self.get_object()
        registration.certificate_issued = True
        registration.save()
        
        return Response({'message': 'Certificate issued'})
    
    @action(detail=True, methods=['post'])
    def verify_payment(self, request, pk=None):
        """Verify payment (staff only)"""
        if not request.user.is_authenticated or request.user.role not in ['superuser', 'faculty_coordinator', 'tech_head']:
            return Response(
                {'error': 'Permission denied'},
                status=status.HTTP_403_FORBIDDEN
            )
        
        registration = self.get_object()
        registration.payment_status = 'paid'
        registration.payment_verified_by = request.user
        registration.payment_date = timezone.now()
        registration.save()
        
        return Response({'message': 'Payment verified'})


class EventSpeakerViewSet(viewsets.ModelViewSet):
    """Event speaker management"""
    
    queryset = EventSpeaker.objects.all()
    serializer_class = EventSpeakerSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """Anyone can view speakers, only events team can modify"""
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [IsEventsTeamOrReadOnly]
        
        return [permission() for permission in permission_classes]


class EventScheduleViewSet(viewsets.ModelViewSet):
    """Event schedule management"""
    
    queryset = EventSchedule.objects.all()
    serializer_class = EventScheduleSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """Anyone can view schedule, only events team can modify"""
        if self.action in ['list', 'retrieve']:
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [IsEventsTeamOrReadOnly]
        
        return [permission() for permission in permission_classes]


class EventFeedbackViewSet(viewsets.ModelViewSet):
    """Event feedback management"""
    
    queryset = EventFeedback.objects.all()
    serializer_class = EventFeedbackSerializer
    permission_classes = [permissions.IsAuthenticated]
    
    def get_permissions(self):
        """Anyone can submit feedback, only staff can view all"""
        if self.action == 'create':
            permission_classes = [permissions.AllowAny]
        else:
            permission_classes = [permissions.IsAuthenticated]
        
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Filter feedback based on user permissions"""
        queryset = EventFeedback.objects.all()
        
        # Staff can see all feedback
        if self.request.user.is_authenticated and self.request.user.role in ['superuser', 'faculty_coordinator', 'tech_head']:
            return queryset
        
        # Regular users can only see their own feedback
        if self.request.user.is_authenticated:
            return queryset.filter(registration__email=self.request.user.email)
        
        return queryset.none()


# Additional utility views with caching
@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def upcoming_events(request):
    """Get upcoming events for display"""
    events = Event.objects.filter(
        status='published',
        is_active=True,
        start_date__gt=timezone.now()
    ).select_related('created_by').only(
        'id', 'title', 'start_date', 'end_date', 'event_type', 'is_featured', 'banner_image'
    ).order_by('start_date')[:5]
    
    serializer = EventListSerializer(events, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def featured_events(request):
    """Get featured events"""
    events = Event.objects.filter(
        status='published',
        is_active=True,
        is_featured=True
    ).select_related('created_by').only(
        'id', 'title', 'start_date', 'end_date', 'event_type', 'banner_image', 'description'
    ).order_by('-start_date')[:3]
    
    serializer = EventListSerializer(events, many=True)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def event_stats(request):
    """Get event statistics"""
    cache_key = 'event_statistics'
    stats = cache.get(cache_key)
    
    if not stats:
        stats = {
            'total_events': Event.objects.count(),
            'published_events': Event.objects.filter(status='published').count(),
            'upcoming_events': Event.objects.filter(
                status='published',
                start_date__gt=timezone.now()
            ).count(),
            'total_registrations': EventRegistration.objects.count()
        }
        cache.set(cache_key, stats, 1800)  # Cache for 30 minutes
    
    return Response(stats)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def quick_register(request):
    """Quick registration for events without authentication"""
    event_id = request.data.get('event_id')
    
    try:
        event = Event.objects.get(id=event_id)
    except Event.DoesNotExist:
        return Response(
            {'error': 'Event not found'},
            status=status.HTTP_404_NOT_FOUND
        )
    
    # Check if registration is open
    if not event.is_registration_open:
        return Response(
            {'error': 'Registration is closed for this event'},
            status=status.HTTP_400_BAD_REQUEST
        )
    
    # Create registration
    serializer = EventRegistrationSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(event=event)
        return Response(
            {
                'message': 'Registration successful',
                'registration': serializer.data
            },
            status=status.HTTP_201_CREATED
        )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([permissions.AllowAny])
def submit_feedback(request):
    """Submit feedback for an event"""
    serializer = EventFeedbackSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save()
        return Response(
            {
                'message': 'Feedback submitted successfully',
                'feedback': serializer.data
            },
            status=status.HTTP_201_CREATED
        )
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
