from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.db.models import F, Q
from django.db import transaction
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
import os
import json
from django.core.cache import cache

from .models import (
    Scheme, Subject, AcademicResource,
    ResourceLike, ACADEMIC_CATEGORIES
)
from .serializers import AcademicResourceSerializer


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
            'description': scheme.description,
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
    """Helper function to get client IP address"""
    x_forwarded_for = request.META.get('HTTP_X_FORWARDED_FOR')
    if x_forwarded_for:
        return x_forwarded_for.split(',')[0]
    return request.META.get('REMOTE_ADDR')

def check_if_liked(resource_id, ip):
    """Check if an IP has liked a resource"""
    return ResourceLike.objects.filter(
        resource_id=resource_id,
        ip_address=ip
    ).exists()

@api_view(['POST'])
@permission_classes([AllowAny])
def toggle_resource_like(request, pk):
    """Toggle like status for a resource"""
    try:
        with transaction.atomic():
            resource = AcademicResource.objects.get(pk=pk, is_approved=True)
            ip = get_client_ip(request)
            
            # Check if already liked
            like_exists = ResourceLike.objects.filter(
                resource=resource,
                ip_address=ip
            ).exists()
            
            if like_exists:
                # Unlike: Remove like record and decrease count
                ResourceLike.objects.filter(
                    resource=resource,
                    ip_address=ip
                ).delete()
                resource.like_count = F('like_count') - 1
                liked = False
            else:
                # Like: Create like record and increase count
                ResourceLike.objects.create(
                    resource=resource,
                    ip_address=ip
                )
                resource.like_count = F('like_count') + 1
                liked = True
            
            resource.save()
            resource.refresh_from_db()
            
            return Response({
                'liked': liked,
                'like_count': resource.like_count
            })
            
    except AcademicResource.DoesNotExist:
        return Response({'error': 'Resource not found'}, status=status.HTTP_404_NOT_FOUND)

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
def download_academic_resource(request, pk):
    """Download academic resource file and increment counter"""
    try:
        with transaction.atomic():
            resource = AcademicResource.objects.get(pk=pk, is_approved=True)
            
            if not resource.file:
                return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)
            
            # Increment download count
            resource.download_count = F('download_count') + 1
            resource.save()
            
            # Get the file path
            file_path = resource.file.path
            
            if not os.path.exists(file_path):
                return Response({'error': 'File not found on disk'}, status=status.HTTP_404_NOT_FOUND)
            
            # Open and serve the file
            with open(file_path, 'rb') as f:
                response = HttpResponse(f.read(), content_type='application/octet-stream')
                response['Content-Disposition'] = f'attachment; filename="{os.path.basename(file_path)}"'
                return response
                
    except AcademicResource.DoesNotExist:
        return Response({'error': 'Resource not found'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
