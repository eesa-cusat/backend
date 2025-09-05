from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from rest_framework import status
from django.db import transaction
from accounts.permissions import IsAcademicsTeamOrReadOnly
from .models import Subject, AcademicResource


@api_view(['POST'])
@permission_classes([IsAcademicsTeamOrReadOnly])
def upload_multiple_notes(request):
    """Upload multiple files for the same module"""
    try:
        subject_id = request.data.get('subject_id')
        category = request.data.get('category', 'notes')
        module_number = request.data.get('module_number', 1)
        title_prefix = request.data.get('title_prefix', 'Academic Resource')
        description = request.data.get('description', '')
        
        files = request.FILES.getlist('files')
        
        if not files:
            return Response({'error': 'No files provided'}, status=status.HTTP_400_BAD_REQUEST)
        
        if not subject_id:
            return Response({'error': 'Subject ID is required'}, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            subject = Subject.objects.get(id=subject_id)
        except Subject.DoesNotExist:
            return Response({'error': 'Subject not found'}, status=status.HTTP_404_NOT_FOUND)
        
        # Validate files
        for file in files:
            if not file.name.lower().endswith('.pdf'):
                return Response({'error': f'File {file.name} is not a PDF'}, status=status.HTTP_400_BAD_REQUEST)
            
            if file.size > 15 * 1024 * 1024:
                return Response({'error': f'File {file.name} exceeds 15MB limit'}, status=status.HTTP_400_BAD_REQUEST)
        
        # Create resources
        created_resources = []
        with transaction.atomic():
            for i, file in enumerate(files):
                file_title = f"{title_prefix} - Part {i + 1}" if len(files) > 1 else title_prefix
                
                resource = AcademicResource(
                    title=file_title,
                    description=description,
                    category=category,
                    subject=subject,
                    module_number=module_number,
                    file=file,
                    uploaded_by=request.user,
                    is_approved=True
                )
                resource.save()
                created_resources.append(resource)
        
        return Response({
            'message': f'Successfully uploaded {len(created_resources)} files',
            'resources': [{
                'id': resource.id,
                'title': resource.title,
                'file_size_mb': resource.file_size_mb
            } for resource in created_resources]
        }, status=status.HTTP_201_CREATED)
        
    except Exception as e:
        return Response({'error': f'Upload failed: {str(e)}'}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


@api_view(['GET'])
@permission_classes([IsAcademicsTeamOrReadOnly])
def admin_resources_list(request):
    """Get list of academic resources for admin panel"""
    resources = AcademicResource.objects.select_related(
        'subject', 'subject__scheme', 'uploaded_by'
    ).order_by('-created_at')
    
    # Apply filters
    category = request.query_params.get('category')
    subject_id = request.query_params.get('subject')
    is_approved = request.query_params.get('is_approved')
    
    if category:
        resources = resources.filter(category=category)
    
    if subject_id:
        resources = resources.filter(subject_id=subject_id)
    
    if is_approved is not None:
        resources = resources.filter(is_approved=is_approved.lower() == 'true')
    
    # Simple pagination
    page_size = min(int(request.query_params.get('page_size', 20)), 100)
    page = int(request.query_params.get('page', 1))
    
    start = (page - 1) * page_size
    end = start + page_size
    
    total_count = resources.count()
    paginated_resources = resources[start:end]
    
    resources_data = []
    for resource in paginated_resources:
        resources_data.append({
            'id': resource.id,
            'title': resource.title,
            'category': resource.get_category_display(),
            'subject': {
                'id': resource.subject.id,
                'name': resource.subject.name,
                'code': resource.subject.code,
                'scheme': resource.subject.scheme.name
            },
            'module_number': resource.module_number,
            'uploaded_by': resource.uploaded_by.username,
            'is_approved': resource.is_approved,
            'file_size_mb': resource.file_size_mb,
            'download_count': resource.download_count,
            'like_count': resource.like_count,
            'created_at': resource.created_at.isoformat()
        })
    
    return Response({
        'resources': resources_data,
        'pagination': {
            'total_count': total_count,
            'page': page,
            'page_size': page_size,
            'total_pages': (total_count + page_size - 1) // page_size
        }
    })


@api_view(['PUT', 'PATCH'])
@permission_classes([IsAcademicsTeamOrReadOnly])
def update_resource(request, pk):
    """Update academic resource"""
    try:
        resource = AcademicResource.objects.get(pk=pk)
    except AcademicResource.DoesNotExist:
        return Response({'error': 'Resource not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Update allowed fields
    allowed_fields = ['title', 'description', 'category', 'module_number', 'is_approved']
    
    for field in allowed_fields:
        if field in request.data:
            setattr(resource, field, request.data[field])
    
    # Handle approval
    if 'is_approved' in request.data and request.data['is_approved'] and not resource.approved_by:
        resource.approved_by = request.user
    
    resource.save()
    
    return Response({
        'message': 'Resource updated successfully',
        'resource': {
            'id': resource.id,
            'title': resource.title,
            'is_approved': resource.is_approved
        }
    })


@api_view(['DELETE'])
@permission_classes([IsAcademicsTeamOrReadOnly])
def delete_resource(request, pk):
    """Delete academic resource"""
    try:
        resource = AcademicResource.objects.get(pk=pk)
        resource.delete()
        return Response({'message': 'Resource deleted successfully'})
    except AcademicResource.DoesNotExist:
        return Response({'error': 'Resource not found'}, status=status.HTTP_404_NOT_FOUND)
