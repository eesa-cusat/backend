from rest_framework import status, permissions, viewsets
from rest_framework.decorators import api_view, permission_classes, action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.utils import timezone
from django.db.models import Q, Count, Prefetch
from accounts.permissions import IsAdminOrTechnicalHead
from .models import Company, PlacementDrive, PlacementApplication, StudentCoordinator, PlacementStatistics
from .serializers import (
    CompanySerializer, CompanyListSerializer,
    PlacementDriveSerializer, PlacementDriveListSerializer,
    PlacementApplicationSerializer, PlacementApplicationListSerializer,
    StudentCoordinatorSerializer, PlacementStatisticsSerializer
)


class PlacementPageNumberPagination(PageNumberPagination):
    """Custom pagination for placement-related listings"""
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 50


class PlacementDriveViewSet(viewsets.ModelViewSet):
    """Optimized ViewSet for Placement Drives with pagination"""
    serializer_class = PlacementDriveSerializer
    pagination_class = PlacementPageNumberPagination
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        queryset = PlacementDrive.objects.filter(
            is_active=True
        ).select_related('company', 'created_by').order_by('-created_at')
        
        # Apply filters
        status_filter = self.request.query_params.get('status')
        if status_filter == 'upcoming':
            queryset = queryset.filter(drive_date__gt=timezone.now())
        elif status_filter == 'registration_open':
            now = timezone.now()
            queryset = queryset.filter(registration_start__lte=now, registration_end__gte=now)
        elif status_filter == 'featured':
            queryset = queryset.filter(is_featured=True)
        
        job_type = self.request.query_params.get('job_type')
        if job_type:
            queryset = queryset.filter(job_type=job_type)
        
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(title__icontains=search) |
                Q(company__name__icontains=search) |
                Q(description__icontains=search)
            )
        
        return queryset

    def get_serializer_class(self):
        """Use different serializers for list vs detail views"""
        if self.action == 'list':
            return PlacementDriveListSerializer
        return PlacementDriveSerializer


class PlacedStudentViewSet(viewsets.ModelViewSet):
    """Optimized ViewSet for Placed Students with pagination"""
    pagination_class = PlacementPageNumberPagination
    permission_classes = [permissions.AllowAny]

    def get_queryset(self):
        from .models import PlacedStudent
        queryset = PlacedStudent.objects.filter(
            is_active=True
        ).select_related('company', 'created_by').order_by('-offer_date', '-package_lpa')
        
        # Apply search filter
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(student_name__icontains=search) |
                Q(company__name__icontains=search) |
                Q(job_title__icontains=search) |
                Q(branch__icontains=search)
            )
        
        # Apply filters
        batch_year = self.request.query_params.get('batch_year')
        if batch_year:
            queryset = queryset.filter(batch_year=batch_year)
        
        branch = self.request.query_params.get('branch')
        if branch:
            queryset = queryset.filter(branch__icontains=branch)
        
        company_id = self.request.query_params.get('company')
        if company_id:
            queryset = queryset.filter(company_id=company_id)
        
        verified_only = self.request.query_params.get('verified_only', 'false').lower() == 'true'
        if verified_only:
            queryset = queryset.filter(is_verified=True)
        
        category = self.request.query_params.get('category')
        if category and category in ['core', 'tech', 'general']:
            queryset = queryset.filter(category=category)
        
        return queryset

    def get_serializer_class(self):
        """Use different serializers for list vs detail views"""
        from .serializers import PlacedStudentSerializer, PlacedStudentListSerializer
        if self.action == 'list':
            return PlacedStudentListSerializer
        return PlacedStudentSerializer


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
        
        # Apply category filter (Core/Tech/General)
        category = request.GET.get('category')
        if category and category in ['core', 'tech', 'general']:
            placed_students = placed_students.filter(category=category)
        
        # Apply status filter (placed students vs past placements)
        status_filter = request.GET.get('status')
        if status_filter == 'placed':
            # Show only currently placed students (recent offers)
            current_year = timezone.now().year
            placed_students = placed_students.filter(offer_date__year=current_year)
        elif status_filter == 'past':
            # Show past placements (older offers)
            current_year = timezone.now().year
            placed_students = placed_students.filter(offer_date__year__lt=current_year)
        
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


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def placement_filters(request):
    """Get available filter options for placements"""
    from .models import PlacedStudent, Company
    
    # Get unique batch years
    batch_years = PlacedStudent.objects.filter(is_active=True).values_list('batch_year', flat=True).distinct().order_by('-batch_year')
    
    # Get unique companies
    companies = Company.objects.filter(is_active=True, placed_students__is_active=True).distinct().order_by('name')
    
    # Get category options
    categories = [
        {'value': 'core', 'label': 'Core'},
        {'value': 'tech', 'label': 'Tech'},
        {'value': 'general', 'label': 'General'},
    ]
    
    # Get status options
    status_options = [
        {'value': 'placed', 'label': 'Placed Students'},
        {'value': 'past', 'label': 'Past Placements'},
    ]
    
    return Response({
        'filters': {
            'batch_years': list(batch_years),
            'companies': [{'id': c.id, 'name': c.name} for c in companies],
            'categories': categories,
            'status_options': status_options,
        }
    })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def placement_statistics_detailed(request):
    """Get detailed placement statistics with charts and analytics"""
    from .models import PlacedStudent, PlacementStatistics
    from django.db.models import Avg, Max, Min, Count
    from django.utils import timezone
    
    current_year = timezone.now().year
    
    # Get overall statistics
    total_placed = PlacedStudent.objects.filter(is_active=True).count()
    current_year_placed = PlacedStudent.objects.filter(
        is_active=True, 
        offer_date__year=current_year
    ).count()
    
    # Package statistics
    package_stats = PlacedStudent.objects.filter(is_active=True).aggregate(
        avg_package=Avg('package_lpa'),
        max_package=Max('package_lpa'),
        min_package=Min('package_lpa')
    )
    
    # Category-wise statistics
    category_stats = PlacedStudent.objects.filter(is_active=True).values('category').annotate(
        count=Count('id'),
        avg_package=Avg('package_lpa'),
        max_package=Max('package_lpa')
    ).order_by('category')
    
    # Year-wise statistics
    year_stats = PlacedStudent.objects.filter(is_active=True).values('offer_date__year').annotate(
        count=Count('id'),
        avg_package=Avg('package_lpa'),
        max_package=Max('package_lpa')
    ).order_by('-offer_date__year')
    
    # Company-wise statistics
    company_stats = PlacedStudent.objects.filter(is_active=True).values(
        'company__name', 'company__logo'
    ).annotate(
        count=Count('id'),
        avg_package=Avg('package_lpa'),
        max_package=Max('package_lpa')
    ).order_by('-count')[:10]  # Top 10 companies
    
    # Job type statistics
    job_type_stats = PlacedStudent.objects.filter(is_active=True).values('job_type').annotate(
        count=Count('id')
    ).order_by('-count')
    
    # Recent placements (last 6 months)
    six_months_ago = timezone.now() - timezone.timedelta(days=180)
    recent_placements = PlacedStudent.objects.filter(
        is_active=True,
        offer_date__gte=six_months_ago
    ).count()
    
    return Response({
        'statistics': {
            'overview': {
                'total_placed': total_placed,
                'current_year_placed': current_year_placed,
                'recent_placements': recent_placements,
                'avg_package': float(package_stats['avg_package'] or 0),
                'max_package': float(package_stats['max_package'] or 0),
                'min_package': float(package_stats['min_package'] or 0),
            },
            'by_category': [
                {
                    'category': stat['category'],
                    'category_display': dict(PlacedStudent._meta.get_field('category').choices)[stat['category']],
                    'count': stat['count'],
                    'avg_package': float(stat['avg_package'] or 0),
                    'max_package': float(stat['max_package'] or 0),
                }
                for stat in category_stats
            ],
            'by_year': [
                {
                    'year': stat['offer_date__year'],
                    'count': stat['count'],
                    'avg_package': float(stat['avg_package'] or 0),
                    'max_package': float(stat['max_package'] or 0),
                }
                for stat in year_stats
            ],
            'top_companies': [
                {
                    'name': stat['company__name'],
                    'logo': stat['company__logo'].url if stat['company__logo'] else None,
                    'count': stat['count'],
                    'avg_package': float(stat['avg_package'] or 0),
                    'max_package': float(stat['max_package'] or 0),
                }
                for stat in company_stats
            ],
            'by_job_type': [
                {
                    'job_type': stat['job_type'],
                    'job_type_display': dict(PlacedStudent._meta.get_field('job_type').choices)[stat['job_type']],
                    'count': stat['count'],
                }
                for stat in job_type_stats
            ],
        }
    })


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def past_recruiters(request):
    """Get list of past recruiters with their placement history"""
    from .models import Company, PlacedStudent
    from django.db.models import Count, Avg, Max
    from django.utils import timezone
    
    current_year = timezone.now().year
    
    # Get companies that have recruited students
    recruiters = Company.objects.filter(
        is_active=True,
        placed_students__is_active=True
    ).distinct().annotate(
        total_recruited=Count('placed_students'),
        avg_package=Avg('placed_students__package_lpa'),
        max_package=Max('placed_students__package_lpa'),
        last_recruitment_year=Max('placed_students__offer_date__year')
    ).order_by('-total_recruited', '-last_recruitment_year')
    
    # Apply filters
    search = request.GET.get('search')
    if search:
        recruiters = recruiters.filter(
            Q(name__icontains=search) |
            Q(industry__icontains=search) |
            Q(location__icontains=search)
        )
    
    # Filter by recruitment year
    year_filter = request.GET.get('year')
    if year_filter:
        recruiters = recruiters.filter(placed_students__offer_date__year=year_filter)
    
    # Filter by category
    category_filter = request.GET.get('category')
    if category_filter and category_filter in ['core', 'tech', 'general']:
        recruiters = recruiters.filter(placed_students__category=category_filter)
    
    # Get detailed information for each recruiter
    recruiter_details = []
    for recruiter in recruiters:
        # Get recent placements (last 3 years)
        recent_placements = PlacedStudent.objects.filter(
            company=recruiter,
            is_active=True,
            offer_date__year__gte=current_year - 3
        ).order_by('-offer_date')[:5]  # Last 5 placements
        
        # Get category breakdown
        category_breakdown = PlacedStudent.objects.filter(
            company=recruiter,
            is_active=True
        ).values('category').annotate(
            count=Count('id'),
            avg_package=Avg('package_lpa')
        ).order_by('category')
        
        recruiter_details.append({
            'id': recruiter.id,
            'name': recruiter.name,
            'logo': recruiter.logo.url if recruiter.logo else None,
            'industry': recruiter.industry,
            'location': recruiter.location,
            'website': recruiter.website,
            'total_recruited': recruiter.total_recruited,
            'avg_package': float(recruiter.avg_package or 0),
            'max_package': float(recruiter.max_package or 0),
            'last_recruitment_year': recruiter.last_recruitment_year,
            'is_current_recruiter': recruiter.last_recruitment_year == current_year,
            'recent_placements': [
                {
                    'student_name': placement.student_name,
                    'job_title': placement.job_title,
                    'package_lpa': float(placement.package_lpa),
                    'offer_date': placement.offer_date,
                    'category': placement.category,
                    'category_display': placement.get_category_display(),
                }
                for placement in recent_placements
            ],
            'category_breakdown': [
                {
                    'category': breakdown['category'],
                    'category_display': dict(PlacedStudent._meta.get_field('category').choices)[breakdown['category']],
                    'count': breakdown['count'],
                    'avg_package': float(breakdown['avg_package'] or 0),
                }
                for breakdown in category_breakdown
            ],
        })
    
    return Response({
        'recruiters': recruiter_details,
        'count': len(recruiter_details),
        'summary': {
            'total_recruiters': recruiters.count(),
            'current_year_recruiters': recruiters.filter(last_recruitment_year=current_year).count(),
            'past_recruiters': recruiters.filter(last_recruitment_year__lt=current_year).count(),
        }
    })
