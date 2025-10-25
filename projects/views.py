from rest_framework import status, permissions, viewsets
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q, Count, Prefetch
from accounts.permissions import IsOwnerOrReadOnly, IsAcademicsTeamOrReadOnly
from utils.redis_cache import ProjectsCache, get_or_set_cache, CacheTTL, invalidate_cache_pattern
import hashlib


class ProjectPageNumberPagination(PageNumberPagination):
    """Custom pagination for projects"""
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 50
from .models import Project, ProjectImage, ProjectVideo, TeamMember
from .serializers import (
    ProjectSerializer, ProjectCreateSerializer, ProjectUpdateSerializer, ProjectListSerializer,
    ProjectImageSerializer, ProjectVideoSerializer
)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def projects_batch_data(request):
    """Optimized batch endpoint for projects page - loads everything at once with Redis caching"""
    import logging
    
    logger = logging.getLogger('eesa_backend.queries')
    
    # Get filter parameters
    category = request.GET.get('category')
    search = request.GET.get('search')
    year = request.GET.get('year')
    
    # Skip cache for search queries
    if search:
        # Original search logic without caching
        base_queryset = Project.objects.select_related('created_by').prefetch_related(
            Prefetch('team_members', 
                    queryset=TeamMember.objects.only('name', 'project_id', 'role')),
            Prefetch('images', 
                    queryset=ProjectImage.objects.only('image', 'project_id')),
        ).filter(is_published=True).only(
            'id', 'title', 'description', 'abstract', 'category', 'created_at', 'is_featured',
            'demo_url', 'github_url', 'created_by__username', 'created_by__first_name',
            'created_by__last_name', 'student_batch', 'academic_year', 'thumbnail', 'project_image'
        )
        
        queryset = base_queryset
        
        if category and category != 'All Categories':
            queryset = queryset.filter(category=category)
        
        if year:
            queryset = queryset.filter(academic_year=year)
        
        search_terms = search.split()[:3]
        search_query = Q()
        for term in search_terms:
            search_query |= (
                Q(title__icontains=term) |
                Q(description__icontains=term) |
                Q(abstract__icontains=term) |
                Q(created_by__first_name__icontains=term) |
                Q(created_by__last_name__icontains=term)
            )
        queryset = queryset.filter(search_query).distinct()
        
        projects = queryset.order_by('-is_featured', '-created_at')
        categories = dict(Project.CATEGORY_CHOICES)
        available_years = Project.objects.filter(
            is_published=True, 
            academic_year__isnull=False
        ).values_list('academic_year', flat=True).distinct().order_by('-academic_year')
        
        featured_projects = projects.filter(is_featured=True)[:4]
        recent_projects = projects[:12]
        total_count = projects.count() if len(projects) <= 100 else '100+'
        
        response_data = {
            'projects': ProjectListSerializer(recent_projects, many=True, context={'request': request}).data,
            'featured_projects': ProjectListSerializer(featured_projects, many=True, context={'request': request}).data,
            'categories': categories,
            'available_years': list(available_years),
            'total_count': total_count,
            'filters': {
                'category': category or 'All Categories',
                'year': year or 'All Years',
                'search': search or ''
            }
        }
        
        return Response(response_data)
    
    # Use cache for non-search queries
    filter_string = f"cat:{category or 'all'}_year:{year or 'all'}"
    cache_key_hash = hashlib.md5(filter_string.encode()).hexdigest()
    cache_key = ProjectsCache.projects_list_key(category=category, year=year, hash=cache_key_hash)
    
    def fetch_projects_batch():
        base_queryset = Project.objects.select_related('created_by').prefetch_related(
            Prefetch('team_members', 
                    queryset=TeamMember.objects.only('name', 'project_id', 'role')),
            Prefetch('images', 
                    queryset=ProjectImage.objects.only('image', 'project_id')),
        ).filter(is_published=True).only(
            'id', 'title', 'description', 'abstract', 'category', 'created_at', 'is_featured',
            'demo_url', 'github_url', 'created_by__username', 'created_by__first_name',
            'created_by__last_name', 'student_batch', 'academic_year', 'thumbnail', 'project_image'
        )
        
        queryset = base_queryset
        
        if category and category != 'All Categories':
            queryset = queryset.filter(category=category)
        
        if year:
            queryset = queryset.filter(academic_year=year)
        
        projects = queryset.order_by('-is_featured', '-created_at')
        categories = dict(Project.CATEGORY_CHOICES)
        available_years = Project.objects.filter(
            is_published=True, 
            academic_year__isnull=False
        ).values_list('academic_year', flat=True).distinct().order_by('-academic_year')
        
        featured_projects = projects.filter(is_featured=True)[:4]
        recent_projects = projects[:12]
        total_count = projects.count() if len(projects) <= 100 else '100+'
        
        return {
            'projects': ProjectListSerializer(recent_projects, many=True, context={'request': request}).data,
            'featured_projects': ProjectListSerializer(featured_projects, many=True, context={'request': request}).data,
            'categories': categories,
            'available_years': list(available_years),
            'total_count': total_count,
            'filters': {
                'category': category or 'All Categories',
                'year': year or 'All Years',
                'search': ''
            }
        }
    
    cached_data = get_or_set_cache(cache_key, fetch_projects_batch, CacheTTL.PROJECTS_LIST)
    logger.info(f"Projects batch data served (cached: {cache_key})")
    return Response(cached_data)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])  # Allow public access
def projects_list(request):
    """List all projects with pagination and comprehensive filtering - public access"""
    # Get filter parameters
    category = request.GET.get('category')
    search = request.GET.get('search')
    creator = request.GET.get('creator')
    team_size = request.GET.get('team_size')
    has_demo = request.GET.get('has_demo')
    has_github = request.GET.get('has_github')
    year = request.GET.get('year')  # New year filter
    
    # Optimized queryset with only necessary fields
    queryset = Project.objects.select_related('created_by').prefetch_related(
        Prefetch('team_members', queryset=TeamMember.objects.only('name', 'project_id')),
        Prefetch('images', queryset=ProjectImage.objects.filter(is_featured=True).only('image', 'project_id'))
    ).only(
        'id', 'title', 'description', 'abstract', 'category', 'student_batch', 'academic_year',
        'is_featured', 'github_url', 'demo_url', 'created_at', 'thumbnail', 'project_image',
        'created_by__username', 'created_by__first_name', 'created_by__last_name'
    )
    
    # Apply filters
    if category and category != 'All Categories':
        queryset = queryset.filter(category=category)
    
    # Year filter (NEW)
    if year:
        queryset = queryset.filter(academic_year=year)
    
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
            Q(abstract__icontains=search) |
            Q(created_by__first_name__icontains=search) |
            Q(created_by__last_name__icontains=search) |
            Q(created_by__username__icontains=search) |
            Q(team_members__name__icontains=search)
        ).distinct()
    
    projects = queryset.order_by('-is_featured', '-created_at')
    
    # Apply pagination
    paginator = ProjectPageNumberPagination()
    page = paginator.paginate_queryset(projects, request)
    if page is not None:
        serializer = ProjectListSerializer(page, many=True, context={'request': request})
        return paginator.get_paginated_response(serializer.data)
    
    # Fallback if pagination fails
    return Response({
        'results': ProjectListSerializer(projects, many=True, context={'request': request}).data,
        'count': projects.count(),
    })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])  # Allow public access
def project_detail(request, pk):
    """Get detailed project information - public access"""
    try:
        project = Project.objects.select_related('created_by').prefetch_related(
            'team_members', 'images', 'videos'
        ).get(pk=pk)
        return Response(ProjectSerializer(project, context={'request': request}).data)
    except Project.DoesNotExist:
        return Response({'error': 'Project not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def project_report(request, pk):
    """Serve project report file with proper Content-Type headers"""
    from django.http import FileResponse, HttpResponse
    import mimetypes
    
    try:
        project = Project.objects.get(pk=pk, is_published=True)
        
        if not project.project_report:
            return Response({
                'error': 'Project report not available'
            }, status=status.HTTP_404_NOT_FOUND)
        
        # Get the file
        report_file = project.project_report
        
        # Determine Content-Type based on file extension
        filename = report_file.name.lower()
        if filename.endswith('.pdf'):
            content_type = 'application/pdf'
        elif filename.endswith('.docx'):
            content_type = 'application/vnd.openxmlformats-officedocument.wordprocessingml.document'
        elif filename.endswith('.doc'):
            content_type = 'application/msword'
        else:
            # Fallback to guessing
            content_type, _ = mimetypes.guess_type(report_file.name)
            if not content_type:
                content_type = 'application/octet-stream'
        
        # For Cloudinary or remote files, redirect
        if hasattr(report_file, 'url'):
            response = HttpResponse(status=302)
            response['Location'] = report_file.url
            response['Content-Type'] = content_type
            # CORS headers for opening in new tab
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Expose-Headers'] = 'Content-Type, Content-Disposition'
            return response
        
        # For local files, serve directly
        try:
            response = FileResponse(report_file.open('rb'), content_type=content_type)
            response['Content-Disposition'] = f'inline; filename="{report_file.name.split("/")[-1]}"'
            # CORS headers
            response['Access-Control-Allow-Origin'] = '*'
            response['Access-Control-Expose-Headers'] = 'Content-Type, Content-Disposition'
            return response
        except Exception as e:
            return Response({
                'error': f'Failed to open report file: {str(e)}'
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except Project.DoesNotExist:
        return Response({
            'error': 'Project not found'
        }, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAcademicsTeamOrReadOnly])
def create_project(request):
    """Create a new project (academics team only)"""
    serializer = ProjectCreateSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        project = serializer.save()
        return Response({
            'message': 'Project created successfully',
            'project': ProjectSerializer(project).data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAcademicsTeamOrReadOnly])
def update_project(request, pk):
    """Update a project (academics team only)"""
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
@permission_classes([IsAcademicsTeamOrReadOnly])
def delete_project(request, pk):
    """Delete a project (academics team only)"""
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
    ).select_related('created_by').prefetch_related(
        Prefetch('images', queryset=ProjectImage.objects.filter(is_featured=True))
    ).only(
        'id', 'title', 'description', 'category', 'created_at',
        'created_by__username', 'created_by__first_name', 'created_by__last_name'
    ).order_by('-created_at')[:6]
    
    return Response({
        'featured_projects': ProjectListSerializer(projects, many=True).data
    })


class ProjectImageViewSet(viewsets.ModelViewSet):
    """ViewSet for managing project images"""
    
    queryset = ProjectImage.objects.all()
    serializer_class = ProjectImageSerializer
    permission_classes = [IsAcademicsTeamOrReadOnly]
    
    def get_queryset(self):
        queryset = ProjectImage.objects.all()
        project_id = self.request.query_params.get('project', None)
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset.order_by('-is_featured', 'created_at')
    
    def perform_create(self, serializer):
        # If this is marked as featured, unset other featured images for the same project
        if serializer.validated_data.get('is_featured', False):
            project = serializer.validated_data['project']
            ProjectImage.objects.filter(project=project, is_featured=True).update(is_featured=False)
        serializer.save()


class ProjectVideoViewSet(viewsets.ModelViewSet):
    """ViewSet for managing project videos"""
    
    queryset = ProjectVideo.objects.all()
    serializer_class = ProjectVideoSerializer
    permission_classes = [IsAcademicsTeamOrReadOnly]
    
    def get_queryset(self):
        queryset = ProjectVideo.objects.all()
        project_id = self.request.query_params.get('project', None)
        if project_id:
            queryset = queryset.filter(project_id=project_id)
        return queryset.order_by('-is_featured', 'created_at')
    
    def perform_create(self, serializer):
        # If this is marked as featured, unset other featured videos for the same project
        if serializer.validated_data.get('is_featured', False):
            project = serializer.validated_data['project']
            ProjectVideo.objects.filter(project=project, is_featured=True).update(is_featured=False)
        serializer.save()
