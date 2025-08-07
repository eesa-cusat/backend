import csv
import io
from django.http import HttpResponse
from django.db.models import Q, Count
from django.utils import timezone
from rest_framework import viewsets, status, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from django_filters.rest_framework import DjangoFilterBackend
from django.contrib.auth import get_user_model

from .models import Alumni
from .serializers import (
    AlumniSerializer, AlumniCreateSerializer,
    BulkAlumniImportSerializer, AlumniStatsSerializer, AlumniSearchSerializer
)
from accounts.permissions import IsOwnerOrReadOnly, IsPeopleTeamOrReadOnly

User = get_user_model()


class AlumniViewSet(viewsets.ModelViewSet):
    """ViewSet for Alumni CRUD operations with CSV import/export"""
    
    queryset = Alumni.objects.all()
    serializer_class = AlumniSerializer
    permission_classes = [IsPeopleTeamOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['year_of_passout', 'employment_status', 'is_verified']
    search_fields = ['full_name', 'email', 'current_company', 'job_title']
    ordering_fields = ['full_name', 'year_of_passout', 'created_at']
    ordering = ['-year_of_passout', 'full_name']
    
    def get_queryset(self):
        queryset = Alumni.objects.filter(is_active=True)
        
        # Apply search filters
        search = self.request.query_params.get('search', None)
        if search:
            queryset = queryset.filter(
                Q(full_name__icontains=search) |
                Q(email__icontains=search) |
                Q(current_company__icontains=search) |
                Q(job_title__icontains=search)
            )
        
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def bulk_import_csv(self, request):
        """Bulk import alumni data from CSV file"""
        serializer = BulkAlumniImportSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        csv_file = serializer.validated_data['csv_file']
        
        try:
            # Read CSV file
            decoded_file = csv_file.read().decode('utf-8')
            io_string = io.StringIO(decoded_file)
            reader = csv.DictReader(io_string)
            
            # Expected CSV headers
            required_headers = [
                'full_name', 'email', 'year_of_passout'
            ]
            optional_headers = [
                'phone_number', 'student_id', 'scheme', 'year_of_joining',
                'specialization', 'cgpa', 'job_title', 'current_company',
                'current_location', 'employment_status',
                'linkedin_profile'
            ]
            
            # Validate headers
            csv_headers = reader.fieldnames or []
            missing_headers = [h for h in required_headers if h not in csv_headers]
            if missing_headers:
                return Response(
                    {'error': f'Missing required headers: {", ".join(missing_headers)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            # Process rows
            successful_imports = 0
            failed_imports = 0
            total_records = 0
            error_log = []
            
            for row_num, row in enumerate(reader, start=1):
                total_records += 1
                try:
                    # Clean and prepare data
                    alumni_data = {}
                    for header in required_headers + optional_headers:
                        if header in row and row[header].strip():
                            value = row[header].strip()
                            
                            # Type conversions
                            if header in ['year_of_passout', 'year_of_joining', 'scheme']:
                                alumni_data[header] = int(value) if value else None
                            elif header == 'cgpa':
                                alumni_data[header] = float(value) if value else None
                            else:
                                alumni_data[header] = value
                    
                    # Set defaults
                    if 'scheme' not in alumni_data and 'year_of_joining' in alumni_data:
                        alumni_data['scheme'] = alumni_data['year_of_joining']
                    if 'year_of_joining' not in alumni_data and 'year_of_passout' in alumni_data:
                        alumni_data['year_of_joining'] = alumni_data['year_of_passout'] - 4
                    
                    # Validate and create
                    create_serializer = AlumniCreateSerializer(data=alumni_data)
                    if create_serializer.is_valid():
                        create_serializer.save(created_by=request.user)
                        successful_imports += 1
                    else:
                        failed_imports += 1
                        error_log.append(f"Row {row_num}: {create_serializer.errors}")
                
                except Exception as e:
                    failed_imports += 1
                    error_log.append(f"Row {row_num}: {str(e)}")
            
            return Response({
                'message': 'CSV import completed',
                'total_records': total_records,
                'successful_imports': successful_imports,
                'failed_imports': failed_imports,
                'errors': error_log[:10]  # Return first 10 errors
            }, status=status.HTTP_201_CREATED)
        
        except Exception as e:
            return Response(
                {'error': f'Failed to process CSV file: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        """Export alumni data to CSV"""
        # Apply filters from query params
        queryset = self.filter_queryset(self.get_queryset())
        
        # Create HTTP response with CSV content type
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="alumni_export_{timezone.now().strftime("%Y%m%d_%H%M%S")}.csv"'
        
        # CSV headers
        headers = [
            'full_name', 'email', 'phone_number', 'student_id',
            'scheme', 'year_of_joining', 'year_of_passout', 'department',
            'specialization', 'cgpa', 'job_title', 'current_company',
            'current_location', 'employment_status',
            'linkedin_profile', 'willing_to_mentor', 'is_verified', 'created_at'
        ]
        
        writer = csv.writer(response)
        writer.writerow(headers)
        
        # Write data rows
        for alumni in queryset:
            row = []
            for header in headers:
                value = getattr(alumni, header, '')
                if header == 'created_at' and value:
                    value = value.strftime('%Y-%m-%d %H:%M:%S')
                elif isinstance(value, bool):
                    value = 'Yes' if value else 'No'
                elif value is None:
                    value = ''
                row.append(str(value))
            writer.writerow(row)
        
        return response
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Get alumni statistics"""
        queryset = Alumni.objects.filter(is_active=True)
        
        # Basic counts
        total_alumni = queryset.count()
        employed_count = queryset.filter(employment_status='employed').count()
        self_employed_count = queryset.filter(employment_status='self_employed').count()
        higher_studies_count = queryset.filter(employment_status='higher_studies').count()
        unemployed_count = queryset.filter(employment_status='unemployed').count()
        
        # Calculate unemployment rate
        unemployment_rate = (unemployed_count / total_alumni * 100) if total_alumni > 0 else 0
        
        # Top companies
        top_companies = list(
            queryset.exclude(current_company__isnull=True)
            .exclude(current_company='')
            .values('current_company')
            .annotate(count=Count('current_company'))
            .order_by('-count')[:10]
        )
        
        # Year-wise distribution
        year_wise_distribution = list(
            queryset.values('year_of_passout')
            .annotate(count=Count('year_of_passout'))
            .order_by('-year_of_passout')
        )
        
        # Department-wise distribution
        department_wise_distribution = list(
            queryset.values('department')
            .annotate(count=Count('department'))
            .order_by('-count')
        )
        
        stats_data = {
            'total_alumni': total_alumni,
            'employed_count': employed_count,
            'self_employed_count': self_employed_count,
            'higher_studies_count': higher_studies_count,
            'unemployment_rate': round(unemployment_rate, 2),
            'top_companies': top_companies,
            'year_wise_distribution': year_wise_distribution,
            'department_wise_distribution': department_wise_distribution
        }
        
        serializer = AlumniStatsSerializer(stats_data)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def entrepreneurship_stats(self, request):
        """Get alumni entrepreneurship statistics"""
        queryset = Alumni.objects.filter(is_active=True)
        total_alumni = queryset.count()
        
        # Count entrepreneurs (both self_employed and entrepreneur status)
        entrepreneurs = queryset.filter(employment_status__in=['self_employed', 'entrepreneur'])
        entrepreneur_count = entrepreneurs.count()
        
        # Calculate entrepreneurship rate
        entrepreneurship_rate = (entrepreneur_count / total_alumni * 100) if total_alumni > 0 else 0
        
        # Get recent entrepreneurs (last 5 years)
        from django.utils import timezone
        current_year = timezone.now().year
        recent_entrepreneurs = entrepreneurs.filter(year_of_passout__gte=current_year - 5)
        
        # Top startup sectors (based on job_title or current_company)
        startup_sectors = list(
            entrepreneurs.exclude(job_title__isnull=True)
            .exclude(job_title='')
            .values('job_title')
            .annotate(count=Count('job_title'))
            .order_by('-count')[:5]
        )
        
        # Entrepreneurship by graduation year
        entrepreneurship_by_year = list(
            entrepreneurs.values('year_of_passout')
            .annotate(count=Count('year_of_passout'))
            .order_by('-year_of_passout')
        )
        
        return Response({
            'total_alumni': total_alumni,
            'total_entrepreneurs': entrepreneur_count,
            'entrepreneurship_rate': round(entrepreneurship_rate, 2),
            'recent_entrepreneurs_count': recent_entrepreneurs.count(),
            'startup_sectors': startup_sectors,
            'entrepreneurship_by_year': entrepreneurship_by_year,
            'success_stories_count': entrepreneur_count  # All entrepreneurs are considered success stories
        })
    
    @action(detail=False, methods=['get'])
    def entrepreneurs(self, request):
        """Get list of entrepreneur alumni"""
        entrepreneurs = Alumni.objects.filter(
            is_active=True,
            employment_status__in=['self_employed', 'entrepreneur']
        ).order_by('-year_of_passout', 'full_name')
        
        serializer = AlumniSerializer(entrepreneurs, many=True)
        return Response({
            'count': entrepreneurs.count(),
            'entrepreneurs': serializer.data
        })
    
    @action(detail=False, methods=['get'])
    def startup_stories(self, request):
        """Get startup success stories (same as entrepreneurs for now)"""
        entrepreneurs = Alumni.objects.filter(
            is_active=True,
            employment_status__in=['self_employed', 'entrepreneur']
        ).order_by('-year_of_passout', 'full_name')
        
        # Format as success stories
        stories = []
        for entrepreneur in entrepreneurs:
            story = {
                'id': entrepreneur.id,
                'name': entrepreneur.full_name,
                'graduation_year': entrepreneur.year_of_passout,
                'company': entrepreneur.current_company or 'Startup Founder',
                'title': entrepreneur.job_title or 'Entrepreneur',
                'location': entrepreneur.current_location,
                'story': f"Alumni of {entrepreneur.year_of_passout}, currently working as {entrepreneur.job_title} at {entrepreneur.current_company}",
                'linkedin': entrepreneur.linkedin_profile
            }
            stories.append(story)
        
        return Response({
            'count': len(stories),
            'success_stories': stories
        })
    
    @action(detail=False, methods=['get'])
    def csv_template(self, request):
        """Download CSV template for bulk import"""
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = 'attachment; filename="alumni_import_template.csv"'
        
        headers = [
            'full_name', 'email', 'phone_number', 'student_id',
            'scheme', 'year_of_joining', 'year_of_passout', 'department',
            'specialization', 'cgpa', 'job_title', 'current_company',
            'current_location', 'employment_status',
            'linkedin_profile'
        ]
        
        writer = csv.writer(response)
        writer.writerow(headers)
        
        # Add sample row
        sample_row = [
            'John Doe', 'john.doe@example.com', '9876543210', 'STU001',
            '2019', '2019', '2023', 'Electrical and Electronics Engineering',
            'VLSI Design', '8.5', 'Software Engineer', 'Tech Company',
            'Bangalore', 'employed', 'https://linkedin.com/in/johndoe'
        ]
        writer.writerow(sample_row)
        
        return response
