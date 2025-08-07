from rest_framework import viewsets, status
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from django.contrib.auth import login, logout
from django.views.decorators.csrf import csrf_exempt, ensure_csrf_cookie
from django.utils.decorators import method_decorator
from django.utils import timezone
from django.middleware.csrf import get_token

from .models import TeamMember, User
from .serializers import (
    TeamMemberSerializer, 
    TeamMemberAdminSerializer,
    UserProfileSerializer, 
    LoginSerializer
)
from .permissions import IsPeopleTeamOrReadOnly


class TeamMemberViewSet(viewsets.ModelViewSet):
    """Team member management with role-based permissions"""
    queryset = TeamMember.objects.filter(is_active=True).order_by('team_type', 'order', 'name')
    
    def get_serializer_class(self):
        if self.action in ['create', 'update', 'partial_update'] and self.request.user.is_authenticated:
            return TeamMemberAdminSerializer
        return TeamMemberSerializer
    
    def get_permissions(self):
        """
        Instantiates and returns the list of permissions that this view requires.
        """
        permission_classes = [IsPeopleTeamOrReadOnly]
        return [permission() for permission in permission_classes]
    
    def get_queryset(self):
        """Return active team members for public, all for admin"""
        if self.request.user.is_authenticated and (
            self.request.user.is_superuser or 
            self.request.user.groups.filter(name='people_team').exists()
        ):
            return TeamMember.objects.all().order_by('team_type', 'order', 'name')
        return TeamMember.objects.filter(is_active=True).order_by('team_type', 'order', 'name')


@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt
def login_view(request):
    """Login endpoint for admin users"""
    serializer = LoginSerializer(data=request.data)
    
    if serializer.is_valid():
        user = serializer.validated_data['user']
        
        # Only allow users with group memberships to login
        if not user.is_superuser and not user.groups.exists():
            return Response({
                'error': 'You do not have permission to access the admin panel.'
            }, status=status.HTTP_403_FORBIDDEN)
        
        login(request, user)
        
        # Return user profile with groups
        profile_serializer = UserProfileSerializer(user)
        return Response({
            'message': 'Login successful',
            'user': profile_serializer.data
        }, status=status.HTTP_200_OK)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def logout_view(request):
    """Logout endpoint"""
    logout(request)
    return Response({
        'message': 'Logout successful'
    }, status=status.HTTP_200_OK)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def me_view(request):
    """Get current authenticated user profile with groups"""
    serializer = UserProfileSerializer(request.user)
    return Response(serializer.data)


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def admin_stats(request):
    """Get admin dashboard statistics"""
    
    # Check if user has any admin permissions
    if not request.user.is_superuser and not request.user.groups.exists():
        return Response({
            'error': 'You do not have permission to access admin statistics.'
        }, status=status.HTTP_403_FORBIDDEN)
    
    stats = {}
    user_groups = [group.name for group in request.user.groups.all()]
    
    # Academics stats
    if request.user.is_superuser or 'academics_team' in user_groups:
        from academics.models import Scheme, Subject, AcademicResource
        stats['academics'] = {
            'schemes': Scheme.objects.count(),
            'subjects': Subject.objects.count(),
            'resources': AcademicResource.objects.count(),
            'pending_approvals': AcademicResource.objects.filter(is_approved=False).count()
        }
    
    # Events stats
    if request.user.is_superuser or 'events_team' in user_groups:
        from events.models import Event, EventRegistration
        stats['events'] = {
            'total_events': Event.objects.count(),
            'upcoming_events': Event.objects.filter(start_date__gt=timezone.now()).count(),
            'total_registrations': EventRegistration.objects.count()
        }
    
    # Careers stats
    if request.user.is_superuser or 'careers_team' in user_groups:
        from careers.models import JobOpportunity, InternshipOpportunity
        stats['careers'] = {
            'job_opportunities': JobOpportunity.objects.filter(is_active=True).count(),
            'internship_opportunities': InternshipOpportunity.objects.filter(is_active=True).count()
        }
    
    # People stats
    if request.user.is_superuser or 'people_team' in user_groups:
        from alumni.models import Alumni
        stats['people'] = {
            'alumni': Alumni.objects.filter(is_active=True).count(),
            'team_members': TeamMember.objects.filter(is_active=True).count()
        }
    
    return Response(stats) 


@api_view(['GET'])
@permission_classes([AllowAny])
@ensure_csrf_cookie
def csrf_token_view(request):
    """Get CSRF token for authenticated requests"""
    return Response({
        'csrfToken': get_token(request),
        'message': 'CSRF token generated'
    }) 