from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.db.models import F, Q
from django.db import transaction
from django.utils import timezone
from django.conf import settings
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
import os
import json
from django.core.cache import cache

from .models import (
    Scheme, Subject, AcademicResource, ResourceLike, ACADEMIC_CATEGORIES
)
from .rate_limiting import rate_limit_by_ip_and_resource
from .serializers import AcademicResourceSerializer


@api_view(['GET'])
@permission_classes([])
def academic_data_combined(request):
    """Get all academic data in one optimized call"""
    cache_key = 'academic_data_combined'
    
    # Try to get from cache first (5 minute cache)
    cached_data = cache.get(cache_key)
    if cached_data:
        return Response(cached_data)
    
    # Schemes
    schemes = Scheme.objects.filter(is_active=True).order_by('name')
    schemes_data = []
    for scheme in schemes:
        schemes_data.append({
            'id': scheme.id,
            'name': scheme.name,
            'year': scheme.year,
            'is_active': scheme.is_active,
        })
    
    # Categories
    categories_data = [
        {
            'id': category[0],
            'name': category[1],
            'category_type': category[0]
        }
        for category in ACADEMIC_CATEGORIES
    ]
    
    # Departments - get from subjects
    departments = Subject.objects.values_list('department', flat=True).distinct().order_by('department')
    departments_data = [dept for dept in departments if dept]
    
    # Subjects grouped by scheme and semester for faster lookup
    subjects = Subject.objects.select_related('scheme').order_by('name')
    subjects_data = {}
    for subject in subjects:
        scheme_id = subject.scheme_id
        semester = subject.semester
        department = subject.department
        
        if scheme_id not in subjects_data:
            subjects_data[scheme_id] = {}
        if semester not in subjects_data[scheme_id]:
            subjects_data[scheme_id][semester] = {}
        if department not in subjects_data[scheme_id][semester]:
            subjects_data[scheme_id][semester][department] = []
            
        subjects_data[scheme_id][semester][department].append({
            'id': subject.id,
            'name': subject.name,
            'code': subject.code,
            'semester': subject.semester,
            'department': subject.department,
            'scheme_name': subject.scheme.name,
        })
    
    combined_data = {
        'schemes': schemes_data,
        'categories': categories_data,
        'departments': departments_data,
        'subjects': subjects_data,
        'message': 'All academic data fetched successfully'
    }
    
    # Cache for 5 minutes
    cache.set(cache_key, combined_data, 300)
    
    return Response(combined_data)


@api_view(['GET'])
@permission_classes([])
def schemes_list(request):
    """List all schemes"""
    schemes = Scheme.objects.all().order_by('name')
    schemes_data = []
    for scheme in schemes:
        schemes_data.append({
            'id': scheme.id,
            'name': scheme.name,
            'year': scheme.year,
            'is_active': scheme.is_active,
        })
    return Response(schemes_data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_scheme(request):
    """Create a new scheme (admin only)"""
    if not request.user.is_superuser:
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    name = request.data.get('name')
    description = request.data.get('description', '')
    
    if not name:
        return Response({'error': 'Name is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    scheme = Scheme.objects.create(name=name, description=description)
    return Response({
        'id': scheme.id,
        'name': scheme.name,
        'message': 'Scheme created successfully'
    }, status=status.HTTP_201_CREATED)


@api_view(['GET'])
@permission_classes([])
def subjects_by_scheme_semester(request):
    """Get subjects by scheme and semester"""
    scheme_id = request.GET.get('scheme')
    semester = request.GET.get('semester')
    
    if not scheme_id or not semester:
        return Response({'error': 'Both scheme and semester are required'}, status=status.HTTP_400_BAD_REQUEST)
    
    subjects = Subject.objects.filter(scheme_id=scheme_id, semester=semester).order_by('name')
    subjects_data = []
    for subject in subjects:
        subjects_data.append({
            'id': subject.id,
            'name': subject.name,
            'code': subject.code,
            'semester': subject.semester,
            'scheme_name': subject.scheme.name,
        })
    return Response(subjects_data)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def create_subject(request):
    """Create a new subject (admin/tech_head only)"""
    if not request.user.is_superuser and request.user.role not in ['admin', 'tech_head']:
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    required_fields = ['name', 'code', 'scheme', 'semester']
    for field in required_fields:
        if field not in request.data:
            return Response({'error': f'{field} is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        scheme = Scheme.objects.get(id=request.data['scheme'])
        subject = Subject.objects.create(
            name=request.data['name'],
            code=request.data['code'],
            scheme=scheme,
            semester=request.data['semester']
        )
        return Response({
            'id': subject.id,
            'name': subject.name,
            'message': 'Subject created successfully'
        }, status=status.HTTP_201_CREATED)
    except Scheme.DoesNotExist:
        return Response({'error': 'Scheme not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([])
def academic_categories_list(request):
    """List all academic categories"""
    categories_data = [
        {
            'id': category[0],
            'name': category[1],
            'category_type': category[0]
        }
        for category in ACADEMIC_CATEGORIES
    ]
    return Response(categories_data)


@api_view(['GET'])
@permission_classes([])
def category_detail(request, category_type):
    """Get category details by type"""
    for category in ACADEMIC_CATEGORIES:
        if category[0] == category_type:
            return Response({
                'id': category[0],
                'name': category[1],
                'category_type': category[0]
            })
    return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([])
def academic_resources_list(request):
    """List academic resources with filtering"""
    resources = AcademicResource.objects.filter(
        is_approved=True
    ).select_related(
        'subject',
        'subject__scheme',
        'uploaded_by'
    )
    
    # Get filter parameters
    category = request.GET.get('category')
    scheme_id = request.GET.get('scheme')
    subject_id = request.GET.get('subject')
    semester = request.GET.get('semester')
    search = request.GET.get('search')
    
    if category:
        resources = resources.filter(category=category)
    
    if scheme_id:
        resources = resources.filter(subject__scheme_id=scheme_id)
    
    if subject_id:
        resources = resources.filter(subject_id=subject_id)
    
    if semester:
        try:
            semester = int(semester)
            resources = resources.filter(subject__semester=semester)
        except (ValueError, TypeError):
            return Response(
                {'error': 'Invalid semester value'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    if search:
        resources = resources.filter(
            Q(title__icontains=search) |
            Q(description__icontains=search) |
            Q(subject__name__icontains=search) |
            Q(subject__code__icontains=search)
        )
    
    resources_data = []
    for resource in resources:
        resources_data.append({
            'id': resource.id,
            'title': resource.title,
            'description': resource.description,
            'file': resource.file.url if resource.file else None,
            'file_size': resource.file_size,
            'file_size_mb': resource.file_size_mb,
            'module_number': resource.module_number if resource.category == 'notes' else None,
            'category': resource.category,
            'subject': {
                'id': resource.subject.id,
                'name': resource.subject.name,
                'code': resource.subject.code,
                'department': resource.subject.department,
                'semester': resource.subject.semester,
                'scheme': {
                    'id': resource.subject.scheme.id,
                    'name': resource.subject.scheme.name,
                    'year': resource.subject.scheme.year
                }
            },
            'uploaded_by': {
                'id': resource.uploaded_by.id,
                'name': f"{resource.uploaded_by.first_name} {resource.uploaded_by.last_name}".strip() or resource.uploaded_by.username
            },
            'created_at': resource.created_at,
            'like_count': resource.like_count,
            'is_liked': check_if_liked(resource.id, get_client_ip(request)),
            'download_count': resource.download_count
        })
    
    return Response({
        'count': len(resources_data),
        'results': resources_data
    })


@api_view(['GET'])
@permission_classes([IsAuthenticated])
def unverified_notes(request):
    """List unverified notes (staff only)"""
    if not request.user.is_staff:
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    resources = AcademicResource.objects.filter(is_approved=False).select_related('subject', 'uploaded_by').order_by('-created_at')
    
    resources_data = []
    for resource in resources:
        resources_data.append({
            'id': resource.id,
            'title': resource.title,
            'description': resource.description,
            'file': resource.file.url if resource.file else '',
            'file_size': resource.file_size,
            'module_number': resource.module_number,
            'exam_type': resource.exam_type,
            'exam_year': resource.exam_year,
            'author': resource.author,
            'created_at': resource.created_at,
            'category': resource.category.category_type,
            'category_name': resource.category.name,
            'subject_name': resource.subject.name,
            'subject_code': resource.subject.code,
            'uploaded_by_name': f"{resource.uploaded_by.first_name} {resource.uploaded_by.last_name}",
        })
    return Response({
        'unverified_notes': resources_data,
        'count': resources.count()
    })


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def approve_note(request, pk):
    """Approve a note (staff only)"""
    if not request.user.is_staff:
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    try:
        resource = AcademicResource.objects.get(pk=pk, is_approved=False)
        resource.is_approved = True
        resource.approved_by = request.user
        resource.approved_at = timezone.now()
        resource.save()
        
        return Response({
            'message': 'Note approved successfully',
            'resource_id': resource.id
        })
    except AcademicResource.DoesNotExist:
        return Response({'error': 'Note not found'}, status=status.HTTP_404_NOT_FOUND)


def get_client_ip(request):
    """
    Helper function to get client IP address with multiple fallbacks
    Handles proxy servers, load balancers, and CDNs
    """
    # Try common proxy headers first
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        # Take the first IP in the chain (original client)
        ip = x_forwarded_for.split(',')[0].strip()
        if ip:
            return ip
    
    # Try other common headers
    x_real_ip = request.META.get('HTTP_X_REAL_IP')
    if x_real_ip:
        return x_real_ip.strip()
    
    # Cloudflare
    cf_connecting_ip = request.META.get('HTTP_CF_CONNECTING_IP')
    if cf_connecting_ip:
        return cf_connecting_ip.strip()
    
    # Fallback to direct connection
    remote_addr = request.META.get('REMOTE_ADDR')
    if remote_addr:
        return remote_addr.strip()
    
    # Last resort
    return '127.0.0.1'

def check_if_liked(resource_id, ip):
    """Check if an IP has liked a resource"""
    return ResourceLike.objects.filter(
        resource_id=resource_id,
        ip_address=ip
    ).exists()

@api_view(['POST'])
@permission_classes([AllowAny])
@csrf_exempt  # Safe for public API - uses IP-based uniqueness constraints
@rate_limit_by_ip_and_resource(max_requests=10, window_seconds=60)  # Prevent abuse
def toggle_resource_like(request, pk):
    """
    Toggle like status for a resource
    
    Security Notes:
    - CSRF exempt because this is a public API endpoint
    - Uses IP-based tracking to ensure one like per IP per resource
    - Database constraints prevent duplicate likes
    - Atomic transactions prevent race conditions
    """
    try:
        with transaction.atomic():
            resource = AcademicResource.objects.select_for_update().get(
                pk=pk, 
                is_approved=True
            )
            ip = get_client_ip(request)
            
            # Validate IP address
            if not ip:
                return Response({
                    'error': 'Unable to determine client IP'
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if already liked by this IP
            like_obj, created = ResourceLike.objects.get_or_create(
                resource=resource,
                ip_address=ip,
                defaults={}
            )
            
            if created:
                # New like created
                resource.like_count = F('like_count') + 1
                liked = True
                message = 'Resource liked successfully'
            else:
                # Like already exists, remove it (unlike)
                like_obj.delete()
                resource.like_count = F('like_count') - 1
                liked = False
                message = 'Resource unliked successfully'
            
            resource.save()
            resource.refresh_from_db()
            
            return Response({
                'liked': liked,
                'like_count': resource.like_count,
                'message': message,
                'resource_id': resource.id
            })
            
    except AcademicResource.DoesNotExist:
        return Response({
            'error': 'Resource not found or not approved'
        }, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({
            'error': 'Failed to update like status',
            'details': str(e) if settings.DEBUG else 'Internal server error'
        }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
            
    except AcademicResource.DoesNotExist:
        return Response({'error': 'Resource not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

@api_view(['GET'])
def academic_resource_detail(request, pk):
    """Get single academic resource"""
    try:
        resource = AcademicResource.objects.select_related(
            'subject',
            'subject__scheme',
            'uploaded_by'
        ).get(pk=pk, is_approved=True)
        
        # Check if the current IP has liked this resource
        ip = get_client_ip(request)
        is_liked = check_if_liked(pk, ip)
        
        resource_data = {
            'id': resource.id,
            'title': resource.title,
            'description': resource.description,
            'file': resource.file.url if resource.file else None,
            'file_size': resource.file_size,
            'file_size_mb': resource.file_size_mb,
            'module_number': resource.module_number if resource.category == 'notes' else None,
            'category': resource.category,
            'subject': {
                'id': resource.subject.id,
                'name': resource.subject.name,
                'code': resource.subject.code,
                'department': resource.subject.department,
                'semester': resource.subject.semester,
                'scheme': {
                    'id': resource.subject.scheme.id,
                    'name': resource.subject.scheme.name,
                    'year': resource.subject.scheme.year
                }
            },
            'uploaded_by': {
                'id': resource.uploaded_by.id,
                'name': f"{resource.uploaded_by.first_name} {resource.uploaded_by.last_name}".strip() or resource.uploaded_by.username
            },
            'created_at': resource.created_at,
            'like_count': resource.like_count,
            'is_liked': is_liked,
            'download_count': resource.download_count
        }
        return Response(resource_data)
    except AcademicResource.DoesNotExist:
        return Response({'error': 'Resource not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_academic_resource(request):
    """Upload new academic resource"""
    serializer = AcademicResourceSerializer(data=request.data, context={'request': request})
    if serializer.is_valid():
        resource = serializer.save(uploaded_by=request.user)
        return Response({
            'id': resource.id,
            'message': 'Resource uploaded successfully'
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([AllowAny])
def get_resource_stats(request, pk):
    """Get resource statistics (likes, downloads) for real-time updates"""
    try:
        resource = AcademicResource.objects.get(pk=pk, is_approved=True)
        ip = get_client_ip(request)
        is_liked = check_if_liked(pk, ip)
        
        return Response({
            'id': resource.id,
            'like_count': resource.like_count,
            'download_count': resource.download_count,
            'is_liked': is_liked,
            'view_count': getattr(resource, 'view_count', 0)
        })
        
    except AcademicResource.DoesNotExist:
        return Response({'error': 'Resource not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([AllowAny])
@rate_limit_by_ip_and_resource(max_requests=20, window_seconds=60)  # Allow more downloads than likes
def download_academic_resource(request, pk):
    """Download academic resource file and increment counter"""
    try:
        with transaction.atomic():
            resource = AcademicResource.objects.get(pk=pk, is_approved=True)
            
            if not resource.file:
                return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Increment download count atomically
            resource.download_count = F('download_count') + 1
            resource.save(update_fields=['download_count'])
            
            # Get the file path
            file_path = resource.file.path
            
            if not os.path.exists(file_path):
                return Response({'error': 'File not found on disk'}, status=status.HTTP_404_NOT_FOUND)
            
            # Get proper filename
            filename = os.path.basename(file_path)
            if not filename:
                filename = f"{resource.title}.pdf"  # fallback filename
            
            # Open and serve the file
            with open(file_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type='application/octet-stream')
                response['Content-Disposition'] = f'attachment; filename="{filename}"'
                response['Content-Length'] = os.path.getsize(file_path)
                return response
                
    except AcademicResource.DoesNotExist:
        return Response({'error': 'Resource not found'}, status=status.HTTP_404_NOT_FOUND)
    except FileNotFoundError:
        return Response({'error': 'File not found on disk'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': f'Download failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
