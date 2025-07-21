from django.shortcuts import render
from django.http import JsonResponse, HttpResponse
from django.views.decorators.csrf import csrf_exempt
from django.contrib.auth.decorators import login_required
from django.db.models import Q
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import IsAuthenticated, AllowAny
from rest_framework.response import Response
from rest_framework import status
import os
import json

from .models import Scheme, Subject, AcademicResource


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
    categories = AcademicCategory.objects.filter(is_active=True).order_by('display_order', 'name')
    categories_data = []
    for category in categories:
        categories_data.append({
            'id': category.id,
            'name': category.name,
            'slug': category.slug,
            'category_type': category.category_type,
            'description': category.description,
            'icon': category.icon,
        })
    return Response(categories_data)


@api_view(['GET'])
@permission_classes([])
def category_detail(request, category_type):
    """Get category details by type"""
    try:
        category = AcademicCategory.objects.get(category_type=category_type, is_active=True)
        return Response({
            'id': category.id,
            'name': category.name,
            'slug': category.slug,
            'category_type': category.category_type,
            'description': category.description,
            'icon': category.icon,
        })
    except AcademicCategory.DoesNotExist:
        return Response({'error': 'Category not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
@permission_classes([])  # Remove authentication requirement
def academic_resources_list(request):
    """List academic resources with filtering"""
    resources = AcademicResource.objects.filter(is_approved=True).select_related('subject', 'uploaded_by')
    
    # Filter by category type
    category_type = request.GET.get('category_type')
    if category_type:
        resources = resources.filter(category__category_type=category_type)
    
    # Filter by other parameters
    scheme_id = request.GET.get('scheme')
    subject_id = request.GET.get('subject')
    semester = request.GET.get('semester')
    search = request.GET.get('search')
    
    if scheme_id:
        resources = resources.filter(scheme_id=scheme_id)
    if subject_id:
        resources = resources.filter(subject_id=subject_id)
    if semester:
        resources = resources.filter(semester=semester)
    if search:
        resources = resources.filter(
            Q(title__icontains=search) | 
            Q(description__icontains=search)
        )
    
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
            'download_count': resource.download_count,
            'created_at': resource.created_at,
            'updated_at': resource.updated_at,
            'category': resource.category.category_type,
            'category_name': resource.category.name,
            'subject_name': resource.subject.name,
            'subject_code': resource.subject.code,
            'is_featured': resource.is_featured,
            'uploaded_by_name': f"{resource.uploaded_by.first_name} {resource.uploaded_by.last_name}",
        })
    return Response(resources_data)


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


@api_view(['GET'])
def academic_resource_detail(request, pk):
    """Get single academic resource"""
    try:
        resource = AcademicResource.objects.get(pk=pk, is_approved=True)
        resource_data = {
            'id': resource.id,
            'title': resource.title,
            'description': resource.description,
            'file': resource.file.url if resource.file else None,
            'file_size': resource.file_size,
            'module_number': resource.module_number,
            'exam_type': resource.exam_type,
            'exam_year': resource.exam_year,
            'author': resource.author,
            'created_at': resource.created_at,
            'updated_at': resource.updated_at
        }
        return Response(resource_data)
    except AcademicResource.DoesNotExist:
        return Response({'error': 'Resource not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['POST'])
@permission_classes([IsAuthenticated])
def upload_academic_resource(request):
    """Upload new academic resource"""
    # Simple validation and creation
    required_fields = ['title', 'category', 'file']
    for field in required_fields:
        if field not in request.data:
            return Response({'error': f'{field} is required'}, status=status.HTTP_400_BAD_REQUEST)
    
    # File validation
    uploaded_file = request.FILES.get('file')
    if not uploaded_file:
        return Response({'error': 'No file uploaded'}, status=status.HTTP_400_BAD_REQUEST)
    
    # Check file extension
    if not uploaded_file.name.lower().endswith('.pdf'):
        return Response({
            'error': 'Only PDF files are allowed. Please upload a PDF document.',
            'help_text': 'Upload only PDF files. Maximum file size: 15MB. Only PDF format is supported for academic resources.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    # Check file size (15MB limit)
    if uploaded_file.size > 15 * 1024 * 1024:
        return Response({
            'error': 'File size must be less than 15MB. Please compress the file or use a smaller document.',
            'help_text': 'Upload only PDF files. Maximum file size: 15MB. Only PDF format is supported for academic resources.'
        }, status=status.HTTP_400_BAD_REQUEST)
    
    try:
        category = AcademicCategory.objects.get(id=request.data['category'])
        resource = AcademicResource.objects.create(
            title=request.data['title'],
            description=request.data.get('description', ''),
            category=category,
            file=uploaded_file,
            uploaded_by=request.user,
            module_number=request.data.get('module_number', 1),
            exam_type=request.data.get('exam_type', ''),
            exam_year=request.data.get('exam_year'),
            author=request.data.get('author', '')
        )
        return Response({'id': resource.id, 'message': 'Resource uploaded successfully'}, 
                       status=status.HTTP_201_CREATED)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([])  # Remove authentication requirement
def download_academic_resource(request, pk):
    """Download academic resource file"""
    try:
        resource = AcademicResource.objects.get(pk=pk, is_approved=True)
        
        if not resource.file:
            return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Increment download count
        resource.download_count += 1
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
