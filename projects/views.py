from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Q, Count
from accounts.permissions import IsOwnerOrReadOnly
from .models import Project
from .serializers import (
    ProjectSerializer, ProjectCreateSerializer, ProjectUpdateSerializer, ProjectListSerializer
)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])  # Allow public access
def projects_list(request):
    """List all projects with comprehensive filtering - public access"""
    # Get filter parameters
    category = request.GET.get('category')
    search = request.GET.get('search')
    creator = request.GET.get('creator')
    team_size = request.GET.get('team_size')
    has_demo = request.GET.get('has_demo')
    has_github = request.GET.get('has_github')
    
    queryset = Project.objects.all()
    
    # Apply filters
    if category and category != 'All Categories':
        queryset = queryset.filter(category=category)
    
    if creator:
        queryset = queryset.filter(created_by__username__icontains=creator)
    
    if team_size:
        try:
            size = int(team_size)
            # Filter by team count (creator + team members)
            queryset = queryset.annotate(
                total_team_count=Count('team_members') + 1
            ).filter(total_team_count=size)
        except ValueError:
            pass
    
    if has_demo and has_demo.lower() == 'true':
        queryset = queryset.filter(demo_url__isnull=False).exclude(demo_url='')
    
    if has_github and has_github.lower() == 'true':
        queryset = queryset.filter(github_url__isnull=False).exclude(github_url='')
    
    # Search functionality
    if search:
        queryset = queryset.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(created_by__first_name__icontains=search) |
            Q(created_by__last_name__icontains=search) |
            Q(created_by__username__icontains=search) |
            Q(team_members__name__icontains=search)
        ).distinct()
    
    projects = queryset.order_by('-created_at').select_related('created_by').prefetch_related(
        'team_members', 'images', 'videos'
    )
    
    # Get available creators for filtering
    available_creators = Project.objects.select_related('created_by').values(
        'created_by__id', 'created_by__username', 'created_by__first_name', 'created_by__last_name'
    ).distinct().order_by('created_by__username')
    
    return Response({
        'projects': ProjectListSerializer(projects, many=True).data,
        'count': projects.count(),
        'filters': {
            'categories': dict(Project.CATEGORY_CHOICES),
            'creators': list(available_creators)
        }
    })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])  # Allow public access
def project_detail(request, pk):
    """Get detailed project information - public access"""
    try:
        project = Project.objects.select_related('created_by').prefetch_related(
            'team_members', 'images', 'videos'
        ).get(pk=pk)
        return Response(ProjectSerializer(project).data)
    except Project.DoesNotExist:
        return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_project(request):
    """Create a new project"""
    serializer = ProjectCreateSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        project = serializer.save()
        return Response({
            'message': 'Project created successfully',
            'project': ProjectSerializer(project).data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT', 'PATCH'])
@permission_classes([permissions.IsAuthenticated])
def update_project(request, pk):
    """Update a project (only by creator)"""
    try:
        project = Project.objects.get(pk=pk)
        
        # Check if user is the creator
        if project.created_by != request.user:
            return Response({
                'error': 'You can only edit your own projects'
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = ProjectUpdateSerializer(project, data=request.data, partial=True)
        if serializer.is_valid():
            project = serializer.save()
            return Response({
                'message': 'Project updated successfully',
                'project': ProjectSerializer(project).data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
    except Project.DoesNotExist:
        return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['DELETE'])
@permission_classes([permissions.IsAuthenticated])
def delete_project(request, pk):
    """Delete a project (only by creator or admin)"""
    try:
        project = Project.objects.get(pk=pk)
        
        # Check if user is the creator or admin
        if project.created_by != request.user and request.user.role != 'admin':
            return Response({
                'error': 'You can only delete your own projects'
            }, status=status.HTTP_403_FORBIDDEN)
        
        project.delete()
        return Response({'message': 'Project deleted successfully'})
        
    except Project.DoesNotExist:
        return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def my_projects(request):
    """Get current user's projects"""
    projects = Project.objects.filter(created_by=request.user).order_by('-created_at')
    return Response({
        'projects': ProjectSerializer(projects, many=True).data
    })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def featured_projects(request):
    """Get featured projects for homepage"""
    # Get featured projects that are published
    projects = Project.objects.filter(
        is_featured=True,
        is_published=True
    ).order_by('-created_at')[:6].select_related('created_by')
    
    return Response({
        'featured_projects': ProjectListSerializer(projects, many=True).data
    })
