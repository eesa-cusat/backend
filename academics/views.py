from django.http import HttpResponse, FileResponse
from django.db.models import F, Q
from django.db import transaction
from django.utils import timezone
from rest_framework.decorators import api_view, permission_classes
from rest_framework.permissions import AllowAny
from django.views.decorators.csrf import csrf_exempt
from rest_framework.throttling import AnonRateThrottle
from rest_framework.decorators import throttle_classes
from rest_framework.response import Response
from rest_framework import status
from django.shortcuts import redirect, get_object_or_404
import os
from django.core.cache import cache

from .models import (
    Scheme, Subject, AcademicResource,
    ResourceLike, ACADEMIC_CATEGORIES, DEPARTMENT_CHOICES
)
from .serializers import AcademicResourceSerializer, AcademicResourceAdminSerializer
from accounts.permissions import IsAcademicsTeamOrReadOnly


@api_view(['GET', 'POST'])
@permission_classes([])
def schemes_list(request):
    """List all schemes (GET) or create new scheme (POST)"""
    if request.method == 'GET':
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

    elif request.method == 'POST':
        # Check permissions for POST
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

        if not request.user.is_superuser and not request.user.groups.filter(name='academics_team').exists():
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        name = request.data.get('name')
        year = request.data.get('year')

        if not name:
            return Response({'error': 'Name is required'}, status=status.HTTP_400_BAD_REQUEST)

        if not year:
            return Response({'error': 'Year is required'}, status=status.HTTP_400_BAD_REQUEST)

        try:
            year = int(year)
        except (ValueError, TypeError):
            return Response({'error': 'Year must be a valid integer'}, status=status.HTTP_400_BAD_REQUEST)

        # Check if a scheme with this year already exists
        if Scheme.objects.filter(year=year).exists():
            return Response({'error': f'Scheme for year {year} already exists'}, status=status.HTTP_400_BAD_REQUEST)

        scheme = Scheme.objects.create(name=name, year=year)
        return Response({
            'id': scheme.id,
            'name': scheme.name,
            'year': scheme.year,
            'message': 'Scheme created successfully'
        }, status=status.HTTP_201_CREATED)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([])
def scheme_detail(request, pk):
    """Get, update, or delete a specific scheme"""
    try:
        scheme = Scheme.objects.get(pk=pk)
    except Scheme.DoesNotExist:
        return Response({'error': 'Scheme not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response({
            'id': scheme.id,
            'name': scheme.name,
            'year': scheme.year,
            'is_active': scheme.is_active,
        })

    elif request.method in ['PUT', 'DELETE']:
        # Check permissions for PUT/DELETE
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

        if not request.user.is_superuser and not request.user.groups.filter(name='academics_team').exists():
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        if request.method == 'PUT':
            name = request.data.get('name', scheme.name)
            year = request.data.get('year', scheme.year)
            is_active = request.data.get('is_active', scheme.is_active)

            if year != scheme.year:
                try:
                    year = int(year)
                    # Check if another scheme with this year already exists
                    if Scheme.objects.filter(year=year).exclude(pk=scheme.pk).exists():
                        return Response({'error': f'Scheme for year {year} already exists'}, status=status.HTTP_400_BAD_REQUEST)
                except (ValueError, TypeError):
                    return Response({'error': 'Year must be a valid integer'}, status=status.HTTP_400_BAD_REQUEST)

            scheme.name = name
            scheme.year = year
            scheme.is_active = is_active
            scheme.save()

            return Response({
                'id': scheme.id,
                'name': scheme.name,
                'year': scheme.year,
                'is_active': scheme.is_active,
                'message': 'Scheme updated successfully'
            })

        elif request.method == 'DELETE':
            # Check if scheme has subjects before deleting
            if scheme.subjects.exists():
                return Response({'error': 'Cannot delete scheme with existing subjects'}, status=status.HTTP_400_BAD_REQUEST)

            scheme.delete()
            return Response({'message': 'Scheme deleted successfully'}, status=status.HTTP_204_NO_CONTENT)


@api_view(['GET', 'POST'])
@permission_classes([])
def subjects_by_scheme_semester(request):
    """Get subjects by scheme and semester (GET) or create new subject (POST)"""
    if request.method == 'GET':
        scheme_id = request.GET.get('scheme')
        semester = request.GET.get('semester')
        department = request.GET.get('department')

        if not scheme_id or not semester:
            return Response({'error': 'Both scheme and semester are required'}, status=status.HTTP_400_BAD_REQUEST)

        subjects = Subject.objects.filter(scheme_id=scheme_id, semester=semester)
        if department:
            valid_departments = {code for code, _ in DEPARTMENT_CHOICES}
            if department not in valid_departments:
                return Response({'error': 'Invalid department'}, status=status.HTTP_400_BAD_REQUEST)
            subjects = subjects.filter(department=department)
        subjects = subjects.order_by('name')
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

    elif request.method == 'POST':
        # Check permissions for POST
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

        if not request.user.is_superuser and not request.user.groups.filter(name='academics_team').exists():
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


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([])
def subject_detail(request, pk):
    """Get, update, or delete a specific subject"""
    try:
        subject = Subject.objects.get(pk=pk)
    except Subject.DoesNotExist:
        return Response({'error': 'Subject not found'}, status=status.HTTP_404_NOT_FOUND)

    if request.method == 'GET':
        return Response({
            'id': subject.id,
            'name': subject.name,
            'code': subject.code,
            'semester': subject.semester,
            'scheme': {
                'id': subject.scheme.id,
                'name': subject.scheme.name,
                'year': subject.scheme.year
            }
        })

    elif request.method in ['PUT', 'DELETE']:
        # Check permissions for PUT/DELETE
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

        if not request.user.is_superuser and not request.user.groups.filter(name='academics_team').exists():
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        if request.method == 'PUT':
            name = request.data.get('name', subject.name)
            code = request.data.get('code', subject.code)
            semester = request.data.get('semester', subject.semester)
            scheme_id = request.data.get('scheme', subject.scheme.id)

            try:
                if scheme_id != subject.scheme.id:
                    scheme = Scheme.objects.get(id=scheme_id)
                    subject.scheme = scheme

                subject.name = name
                subject.code = code
                subject.semester = semester
                subject.save()

                return Response({
                    'id': subject.id,
                    'name': subject.name,
                    'code': subject.code,
                    'semester': subject.semester,
                    'message': 'Subject updated successfully'
                })
            except Scheme.DoesNotExist:
                return Response({'error': 'Scheme not found'}, status=status.HTTP_404_NOT_FOUND)

        elif request.method == 'DELETE':
            # Check if subject has resources before deleting
            if subject.resources.exists():
                return Response({'error': 'Cannot delete subject with existing resources'}, status=status.HTTP_400_BAD_REQUEST)

            subject.delete()
            return Response({'message': 'Subject deleted successfully'}, status=status.HTTP_204_NO_CONTENT)


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


@api_view(['GET', 'POST'])
@permission_classes([])
def academic_resources_list(request):
    """List academic resources with filtering (GET) or upload new resource (POST)"""
    if request.method == 'GET':
        # Check if user is authenticated and has admin permissions
        is_admin = (request.user.is_authenticated and
                   (request.user.is_superuser or
                    request.user.groups.filter(name='academics_team').exists()))

        # For public users, only show approved resources
        # For admins, show all resources or filter by approval status
        if is_admin:
            resources = AcademicResource.objects.all()
            # Allow filtering by approval status for admins
            is_approved = request.GET.get('is_approved')
            if is_approved is not None:
                if is_approved.lower() == 'true':
                    resources = resources.filter(is_approved=True)
                elif is_approved.lower() == 'false':
                    resources = resources.filter(is_approved=False)
        else:
            # Public users only see approved resources
            resources = AcademicResource.objects.filter(is_approved=True)

        resources = resources.select_related(
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
        department = request.GET.get('department')

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

        if department:
            valid_departments = {code for code, _ in DEPARTMENT_CHOICES}
            if department not in valid_departments:
                return Response({'error': 'Invalid department'}, status=status.HTTP_400_BAD_REQUEST)
            resources = resources.filter(subject__department=department)

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
                'file': resource.file_url,
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

    elif request.method == 'POST':
        # Check permissions for POST
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

        if not request.user.is_superuser and not request.user.groups.filter(name='academics_team').exists():
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

        # Use admin serializer for admin users
        is_admin = (request.user.is_superuser or
                   request.user.groups.filter(name='academics_team').exists())

        if is_admin:
            serializer = AcademicResourceAdminSerializer(data=request.data, context={'request': request})
        else:
            serializer = AcademicResourceSerializer(data=request.data, context={'request': request})

        if serializer.is_valid():
            resource = serializer.save(uploaded_by=request.user)
            return Response({
                'id': resource.id,
                'is_approved': resource.is_approved,
                'message': 'Resource uploaded successfully'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET'])
@permission_classes([IsAcademicsTeamOrReadOnly])
def unverified_notes(request):
    """List unverified notes (academics team only)"""
    # Check if user has academics team permission (handled by permission class)
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
            'category': resource.category,
            'subject_name': resource.subject.name,
            'subject_code': resource.subject.code,
            'uploaded_by_name': f"{resource.uploaded_by.first_name} {resource.uploaded_by.last_name}".strip() or resource.uploaded_by.username,
            'created_at': resource.created_at,
        })
    return Response({
        'unverified_notes': resources_data,
        'count': resources.count()
    })


@api_view(['POST'])
@permission_classes([IsAcademicsTeamOrReadOnly])
def approve_note(request, pk):
    """Approve a note (academics team only)"""
    # Permission is handled by the permission class
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


@api_view(['POST'])
@permission_classes([IsAcademicsTeamOrReadOnly])
def toggle_approval_status(request, pk):
    """Toggle approval status of a resource (academics team only)"""
    try:
        resource = AcademicResource.objects.get(pk=pk)

        # Toggle the approval status
        if resource.is_approved:
            resource.is_approved = False
            resource.approved_by = None
            resource.approved_at = None
            message = 'Resource marked as unapproved'
        else:
            resource.is_approved = True
            resource.approved_by = request.user
            resource.approved_at = timezone.now()
            message = 'Resource approved successfully'

        resource.save()

        return Response({
            'message': message,
            'resource_id': resource.id,
            'is_approved': resource.is_approved
        })
    except AcademicResource.DoesNotExist:
        return Response({'error': 'Resource not found'}, status=status.HTTP_404_NOT_FOUND)


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
    """Toggle like status for a resource with rate-limiting"""
    try:
        ip = get_client_ip(request)
        session_key = request.session.session_key or 'no-session'
        rate_key = f"like-rate:{ip}:{session_key}"
        current_count = cache.get(rate_key, 0)
        if current_count >= 10:
            return Response({'error': 'Rate limit exceeded. Try again later.'}, status=status.HTTP_429_TOO_MANY_REQUESTS)
        cache.set(rate_key, current_count + 1, timeout=60)
        with transaction.atomic():
            resource = AcademicResource.objects.get(pk=pk, is_approved=True)
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


@api_view(['GET', 'PUT', 'DELETE'])
def academic_resource_detail(request, pk):
    """Get, update, or delete single academic resource"""
    try:
        resource = AcademicResource.objects.select_related(
            'subject',
            'subject__scheme',
            'uploaded_by'
        ).get(pk=pk)

        # For GET requests, only show approved resources to public
        if request.method == 'GET' and not resource.is_approved:
            if not request.user.is_authenticated or (not request.user.is_superuser and not request.user.groups.filter(name='academics_team').exists()):
                return Response({'error': 'Resource not found'}, status=status.HTTP_404_NOT_FOUND)

        if request.method == 'GET':
            # Check if the current IP has liked this resource
            ip = get_client_ip(request)
            is_liked = check_if_liked(pk, ip)

            resource_data = {
                'id': resource.id,
                'title': resource.title,
                'description': resource.description,
                'file': resource.file_url,
                'file_size': resource.file_size,
                'file_size_mb': resource.file_size_mb,
                'module_number': resource.module_number if resource.category == 'notes' else None,
                'category': resource.category,
                'is_approved': resource.is_approved,
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

        elif request.method in ['PUT', 'DELETE']:
            # Check permissions for PUT/DELETE
            if not request.user.is_authenticated:
                return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)

            # Only allow resource owner, academics team, or superuser to modify
            if not (request.user.is_superuser or
                    request.user.groups.filter(name='academics_team').exists() or
                    resource.uploaded_by == request.user):
                return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)

            if request.method == 'PUT':
                # Use admin serializer for admin users, regular serializer for resource owners
                is_admin = (request.user.is_superuser or
                           request.user.groups.filter(name='academics_team').exists())

                if is_admin:
                    serializer = AcademicResourceAdminSerializer(resource, data=request.data, partial=True, context={'request': request})
                else:
                    serializer = AcademicResourceSerializer(resource, data=request.data, partial=True, context={'request': request})

                if serializer.is_valid():
                    updated_resource = serializer.save()
                    return Response({
                        'id': updated_resource.id,
                        'title': updated_resource.title,
                        'is_approved': updated_resource.is_approved,
                        'message': 'Resource updated successfully'
                    })
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

            elif request.method == 'DELETE':
                # Delete the file if it exists
                if resource.file:
                    try:
                        resource.file.delete()
                    except Exception:
                        pass  # Continue even if file deletion fails

                resource.delete()
                return Response({'message': 'Resource deleted successfully'}, status=status.HTTP_204_NO_CONTENT)

    except AcademicResource.DoesNotExist:
        return Response({'error': 'Resource not found'}, status=status.HTTP_404_NOT_FOUND)


@api_view(['GET'])
def download_academic_resource(request, pk):
    """Download academic resource file and increment counter"""
    try:
        resource = get_object_or_404(AcademicResource, pk=pk, is_approved=True)

        if not resource.file:
            return Response({'error': 'File not found'}, status=status.HTTP_404_NOT_FOUND)

        # Increment download count using F() expression for atomic update
        resource.download_count = F('download_count') + 1
        resource.save(update_fields=['download_count'])
        resource.refresh_from_db()

        # If Cloudinary URL, redirect to it for optimized delivery
        if 'res.cloudinary.com' in str(resource.file):
            return redirect(resource.file.url)

        # Fallback: serve local file
        file_path = resource.file.path
        response = FileResponse(open(file_path, 'rb'), as_attachment=True, filename=os.path.basename(file_path))
        return response

    except AcademicResource.DoesNotExist:
        return Response({'error': 'Resource not found'}, status=status.HTTP_404_NOT_FOUND)
    except FileNotFoundError:
        return Response({'error': 'File not found on disk'}, status=status.HTTP_404_NOT_FOUND)
    except Exception as e:
        return Response({'error': str(e)}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)