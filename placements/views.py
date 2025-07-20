from rest_framework import status, permissions
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.utils import timezone
from django.db.models import Q, Count
from accounts.permissions import IsAdminOrTechnicalHead
from .models import Company, PlacementDrive, PlacementApplication, StudentCoordinator, PlacementStatistics
from .serializers import (
    CompanySerializer, CompanyListSerializer,
    PlacementDriveSerializer, PlacementDriveListSerializer,
    PlacementApplicationSerializer, PlacementApplicationListSerializer,
    StudentCoordinatorSerializer, PlacementStatisticsSerializer
)


# Company views
@api_view(['GET', 'POST'])
@permission_classes([permissions.AllowAny])  # Changed to allow public access
def companies_list(request):
    """List all companies or create a new company"""
    if request.method == 'GET':
        companies = Company.objects.filter(is_active=True).order_by('name')
        
        # Apply search filter
        search = request.GET.get('search')
        if search:
            companies = companies.filter(
                Q(name__icontains=search) |
                Q(industry__icontains=search) |
                Q(location__icontains=search)
            )
        
        # Apply verified filter
        verified_only = request.GET.get('verified_only', 'false').lower() == 'true'
        if verified_only:
            companies = companies.filter(is_verified=True)
        
        serializer = CompanySerializer(companies, many=True)
        return Response({
            'companies': serializer.data,
            'count': companies.count()
        })
    
    elif request.method == 'POST':
        # Only admin/tech_head can create companies
        if request.user.role not in ['admin', 'tech_head']:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = CompanySerializer(data=request.data)
        if serializer.is_valid():
            company = serializer.save(created_by=request.user)
            return Response({
                'message': 'Company created successfully',
                'company': CompanySerializer(company).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def company_detail(request, pk):
    """Get, update or delete a company"""
    try:
        company = Company.objects.get(pk=pk)
    except Company.DoesNotExist:
        return Response({'error': 'Company not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = CompanySerializer(company)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        # Only admin/tech_head can update companies
        if request.user.role not in ['admin', 'tech_head']:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = CompanySerializer(company, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Company updated successfully',
                'company': serializer.data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        # Only admin can delete companies
        if request.user.role != 'admin':
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        company.is_active = False
        company.save()
        return Response({'message': 'Company deleted successfully'})


# Placement Drive views
@api_view(['GET', 'POST'])
@permission_classes([permissions.AllowAny])  # Explicitly allow any for GET, check auth in POST
def placement_drives_list(request):
    """List all placement drives or create a new drive"""
    if request.method == 'GET':
        # Public access for GET requests
        drives = PlacementDrive.objects.filter(is_active=True).select_related('company')
        
        # Apply filters
        status_filter = request.GET.get('status')
        if status_filter == 'upcoming':
            drives = drives.filter(drive_date__gt=timezone.now())
        elif status_filter == 'registration_open':
            now = timezone.now()
            drives = drives.filter(registration_start__lte=now, registration_end__gte=now)
        elif status_filter == 'featured':
            drives = drives.filter(is_featured=True)
        
        job_type = request.GET.get('job_type')
        if job_type:
            drives = drives.filter(job_type=job_type)
        
        search = request.GET.get('search')
        if search:
            drives = drives.filter(
                Q(title__icontains=search) |
                Q(company__name__icontains=search) |
                Q(description__icontains=search)
            )
        
        serializer = PlacementDriveListSerializer(drives, many=True)
        return Response({
            'drives': serializer.data,
            'count': drives.count()
        })
    
    elif request.method == 'POST':
        # Require authentication for POST requests
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
            
        # Only placement coordinators/admin can create drives
        if request.user.role not in ['admin', 'tech_head']:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = PlacementDriveSerializer(data=request.data)
        if serializer.is_valid():
            drive = serializer.save(created_by=request.user)
            return Response({
                'message': 'Placement drive created successfully',
                'drive': PlacementDriveSerializer(drive).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def placement_drive_detail(request, pk):
    """Get, update or delete a placement drive"""
    try:
        drive = PlacementDrive.objects.select_related('company', 'created_by').get(pk=pk)
    except PlacementDrive.DoesNotExist:
        return Response({'error': 'Placement drive not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        serializer = PlacementDriveSerializer(drive)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        # Only admin/tech_head can update drives
        if request.user.role not in ['admin', 'tech_head']:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = PlacementDriveSerializer(drive, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Placement drive updated successfully',
                'drive': serializer.data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        # Only admin can delete drives
        if request.user.role != 'admin':
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        drive.is_active = False
        drive.save()
        return Response({'message': 'Placement drive deleted successfully'})


# Application views
@api_view(['GET', 'POST'])
@permission_classes([permissions.IsAuthenticated])
def placement_applications_list(request):
    """List placement applications or create a new application"""
    if request.method == 'GET':
        # Students can only see their own applications
        if request.user.role == 'student':
            applications = PlacementApplication.objects.filter(student=request.user)
        else:
            # Admin/staff can see all applications
            applications = PlacementApplication.objects.all()
        
        applications = applications.select_related('drive__company', 'student').order_by('-applied_at')
        
        # Apply filters
        status_filter = request.GET.get('status')
        if status_filter:
            applications = applications.filter(status=status_filter)
        
        drive_id = request.GET.get('drive_id')
        if drive_id:
            applications = applications.filter(drive_id=drive_id)
        
        serializer = PlacementApplicationListSerializer(applications, many=True)
        return Response({
            'applications': serializer.data,
            'count': applications.count()
        })
    
    elif request.method == 'POST':
        # Only students can apply
        if request.user.role != 'student':
            return Response({'error': 'Only students can apply for placements'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = PlacementApplicationSerializer(data=request.data)
        if serializer.is_valid():
            # Check if student already applied
            drive_id = serializer.validated_data['drive_id']
            if PlacementApplication.objects.filter(drive_id=drive_id, student=request.user).exists():
                return Response({'error': 'You have already applied for this drive'}, status=status.HTTP_400_BAD_REQUEST)
            
            # Check if registration is open
            try:
                drive = PlacementDrive.objects.get(id=drive_id)
                if not drive.is_registration_open:
                    return Response({'error': 'Registration is closed for this drive'}, status=status.HTTP_400_BAD_REQUEST)
            except PlacementDrive.DoesNotExist:
                return Response({'error': 'Drive not found'}, status=status.HTTP_404_NOT_FOUND)
            
            application = serializer.save(student=request.user)
            return Response({
                'message': 'Application submitted successfully',
                'application': PlacementApplicationSerializer(application).data
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def placement_application_detail(request, pk):
    """Get, update or delete a placement application"""
    try:
        application = PlacementApplication.objects.select_related('drive__company', 'student').get(pk=pk)
    except PlacementApplication.DoesNotExist:
        return Response({'error': 'Application not found'}, status=status.HTTP_404_NOT_FOUND)
    
    # Check permissions
    if request.user.role == 'student' and application.student != request.user:
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    if request.method == 'GET':
        serializer = PlacementApplicationSerializer(application)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        # Students can only update their own applications, staff can update status
        if request.user.role == 'student':
            if application.student != request.user:
                return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
            # Students can only update certain fields
            allowed_fields = ['cover_letter', 'resume', 'additional_documents']
            update_data = {k: v for k, v in request.data.items() if k in allowed_fields}
        else:
            # Staff can update all fields
            update_data = request.data
        
        serializer = PlacementApplicationSerializer(application, data=update_data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response({
                'message': 'Application updated successfully',
                'application': serializer.data
            })
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        # Students can withdraw, admin can delete
        if request.user.role == 'student':
            if application.student != request.user:
                return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
            application.status = 'withdrawn'
            application.save()
            return Response({'message': 'Application withdrawn successfully'})
        elif request.user.role in ['admin', 'tech_head']:
            application.delete()
            return Response({'message': 'Application deleted successfully'})
        else:
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)


# Statistics views
@api_view(['GET'])
@permission_classes([permissions.AllowAny])  # Changed to allow public access
def placement_statistics(request):
    """Get placement statistics"""
    stats = PlacementStatistics.objects.all().order_by('-batch_year')
    
    # Apply filters
    batch_year = request.GET.get('batch_year')
    if batch_year:
        stats = stats.filter(batch_year=batch_year)
    
    academic_year = request.GET.get('academic_year')
    if academic_year:
        stats = stats.filter(academic_year=academic_year)
    
    # Convert to list with calculated fields
    results = []
    for stat in stats:
        results.append({
            'id': stat.id,
            'academic_year': stat.academic_year,
            'batch_year': stat.batch_year,
            'branch': stat.branch,
            'total_students': stat.total_students,
            'total_placed': stat.total_placed,
            'placement_percentage': stat.placement_percentage,
            'highest_package': float(stat.highest_package),
            'average_package': float(stat.average_package),
            'median_package': float(stat.median_package),
            'total_companies_visited': stat.total_companies_visited,
            'total_offers': stat.total_offers,
            'created_at': stat.created_at,
            'updated_at': stat.updated_at
        })
    
    return Response({
        'statistics': results,
        'count': len(results)
    })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def placement_overview(request):
    """Get placement overview for public display"""
    current_year = timezone.now().year
    
    # Current year stats
    current_stats = PlacementStatistics.objects.filter(batch_year=current_year)
    
    # Active drives
    active_drives = PlacementDrive.objects.filter(
        is_active=True,
        drive_date__gte=timezone.now()
    ).count()
    
    # Registration open drives
    now = timezone.now()
    open_registrations = PlacementDrive.objects.filter(
        is_active=True,
        registration_start__lte=now,
        registration_end__gte=now
    ).count()
    
    # Companies visited this year
    companies_count = Company.objects.filter(
        is_active=True,
        placement_drives__drive_date__year=current_year
    ).distinct().count()
    
    return Response({
        'overview': {
            'active_drives': active_drives,
            'open_registrations': open_registrations,
            'companies_visited': companies_count,
            'current_year': current_year
        },
        'current_year_stats': PlacementStatisticsSerializer(current_stats, many=True).data
    })


# Placed Students views
@api_view(['GET', 'POST'])
@permission_classes([permissions.AllowAny])  # Explicitly allow any for GET, check auth in POST
def placed_students_list(request):
    """List all placed students or create a new placed student record"""
    if request.method == 'GET':
        # Public access for GET requests
        from .models import PlacedStudent
        placed_students = PlacedStudent.objects.filter(is_active=True).order_by('-offer_date', '-package_lpa')
        
        # Apply search filter
        search = request.GET.get('search')
        if search:
            placed_students = placed_students.filter(
                Q(student_name__icontains=search) |
                Q(company__name__icontains=search) |
                Q(job_title__icontains=search) |
                Q(branch__icontains=search)
            )
        
        # Apply batch year filter
        batch_year = request.GET.get('batch_year')
        if batch_year:
            placed_students = placed_students.filter(batch_year=batch_year)
        
        # Apply branch filter
        branch = request.GET.get('branch')
        if branch:
            placed_students = placed_students.filter(branch__icontains=branch)
        
        # Apply company filter
        company_id = request.GET.get('company')
        if company_id:
            placed_students = placed_students.filter(company_id=company_id)
        
        # Apply verified filter
        verified_only = request.GET.get('verified_only', 'false').lower() == 'true'
        if verified_only:
            placed_students = placed_students.filter(is_verified=True)
        
        from .serializers import PlacedStudentListSerializer
        serializer = PlacedStudentListSerializer(placed_students, many=True)
        return Response({
            'placed_students': serializer.data,
            'count': placed_students.count()
        })
    
    elif request.method == 'POST':
        # Require authentication for POST requests
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
            
        # Only admin/tech_head/placement_coordinator can create placed student records
        if request.user.role not in ['admin', 'tech_head'] and not hasattr(request.user, 'placement_coordinator'):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        from .serializers import PlacedStudentSerializer
        serializer = PlacedStudentSerializer(data=request.data)
        if serializer.is_valid():
            serializer.save(created_by=request.user)
            return Response(serializer.data, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([permissions.IsAuthenticated])
def placed_student_detail(request, pk):
    """Retrieve, update or delete a placed student record"""
    try:
        from .models import PlacedStudent
        placed_student = PlacedStudent.objects.get(pk=pk)
    except PlacedStudent.DoesNotExist:
        return Response({'error': 'Placed student not found'}, status=status.HTTP_404_NOT_FOUND)
    
    if request.method == 'GET':
        from .serializers import PlacedStudentSerializer
        serializer = PlacedStudentSerializer(placed_student)
        return Response(serializer.data)
    
    elif request.method == 'PUT':
        # Only admin/tech_head/placement_coordinator can update
        if request.user.role not in ['admin', 'tech_head'] and not hasattr(request.user, 'placement_coordinator'):
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        from .serializers import PlacedStudentSerializer
        serializer = PlacedStudentSerializer(placed_student, data=request.data, partial=True)
        if serializer.is_valid():
            serializer.save()
            return Response(serializer.data)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
    
    elif request.method == 'DELETE':
        # Only admin can delete
        if request.user.role != 'admin':
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        placed_student.is_active = False
        placed_student.save()
        return Response(status=status.HTTP_204_NO_CONTENT)


@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def placed_student_create(request):
    """Create a new placed student record with file uploads"""
    # Only admin/tech_head/placement_coordinator can create
    if request.user.role not in ['admin', 'tech_head'] and not hasattr(request.user, 'placement_coordinator'):
        return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
    
    from .serializers import PlacedStudentSerializer
    serializer = PlacedStudentSerializer(data=request.data)
    if serializer.is_valid():
        serializer.save(created_by=request.user)
        return Response({
            'message': 'Placed student record created successfully',
            'data': serializer.data
        }, status=status.HTTP_201_CREATED)
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
