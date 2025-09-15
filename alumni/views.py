import csv
import io
from django.http import HttpResponse
from django.db.models import Q, Count, Prefetch
from django.utils import timezone
from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser
from rest_framework.pagination import PageNumberPagination
from django_filters.rest_framework import DjangoFilterBackend

from .models import Alumni, AlumniBatch
from .serializers import (
    AlumniSerializer, AlumniCreateSerializer, BulkAlumniImportSerializer,
    AlumniStatsSerializer, AlumniBatchSerializer, AlumniBatchListSerializer, 
    AlumniBatchStatsSerializer, AlumniListSerializer
)
from accounts.permissions import IsPeopleTeamOrReadOnly


class AlumniPageNumberPagination(PageNumberPagination):
    """Custom pagination for alumni listing"""
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 50


class AlumniViewSet(viewsets.ModelViewSet):
    """Alumni CRUD operations with CSV import/export and optimized pagination"""
    
    queryset = Alumni.objects.select_related('batch', 'created_by').filter(is_active=True)
    serializer_class = AlumniSerializer
    permission_classes = [IsPeopleTeamOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ['batch', 'employment_status', 'is_verified']
    search_fields = ['full_name', 'email', 'current_company']
    ordering = ['-created_at']
    pagination_class = AlumniPageNumberPagination

    def get_serializer_class(self):
        """Use different serializers for list vs detail views"""
        if self.action == 'list':
            return AlumniListSerializer
        return AlumniSerializer
    
    def get_queryset(self):
        queryset = self.queryset
        search = self.request.query_params.get('search')
        if search:
            queryset = queryset.filter(
                Q(full_name__icontains=search) |
                Q(email__icontains=search) |
                Q(current_company__icontains=search)
            )
        return queryset
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['post'], parser_classes=[MultiPartParser, FormParser])
    def bulk_import_csv(self, request):
        """Bulk import alumni from CSV"""
        serializer = BulkAlumniImportSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        
        try:
            csv_file = serializer.validated_data['csv_file']
            decoded_file = csv_file.read().decode('utf-8')
            reader = csv.DictReader(io.StringIO(decoded_file))
            
            required_headers = ['full_name', 'email', 'batch_year_range']
            csv_headers = reader.fieldnames or []
            missing_headers = [h for h in required_headers if h not in csv_headers]
            
            if missing_headers:
                return Response(
                    {'error': f'Missing headers: {", ".join(missing_headers)}'},
                    status=status.HTTP_400_BAD_REQUEST
                )
            
            successful_imports = 0
            errors = []
            
            for row_num, row in enumerate(reader, start=1):
                try:
                    batch_year_range = row.get('batch_year_range', '').strip()
                    if batch_year_range:
                        batch, _ = AlumniBatch.objects.get_or_create(
                            batch_year_range=batch_year_range,
                            defaults={'batch_name': f"Batch {batch_year_range}"}
                        )
                        
                        alumni_data = {
                            'full_name': row.get('full_name', '').strip(),
                            'email': row.get('email', '').strip(),
                            'batch': batch.id
                        }
                        
                        create_serializer = AlumniCreateSerializer(data=alumni_data)
                        if create_serializer.is_valid():
                            create_serializer.save(created_by=request.user)
                            successful_imports += 1
                        else:
                            errors.append(f"Row {row_num}: {create_serializer.errors}")
                except Exception as e:
                    errors.append(f"Row {row_num}: {str(e)}")
            
            return Response({
                'successful_imports': successful_imports,
                'errors': errors[:5]  # First 5 errors only
            }, status=status.HTTP_201_CREATED)
            
        except Exception as e:
            return Response(
                {'error': f'CSV processing failed: {str(e)}'},
                status=status.HTTP_400_BAD_REQUEST
            )
    
    @action(detail=False, methods=['get'])
    def export_csv(self, request):
        """Export alumni to CSV"""
        queryset = self.filter_queryset(self.get_queryset())
        response = HttpResponse(content_type='text/csv')
        response['Content-Disposition'] = f'attachment; filename="alumni_{timezone.now().strftime("%Y%m%d")}.csv"'
        
        writer = csv.writer(response)
        writer.writerow(['full_name', 'email', 'batch_year_range', 'employment_status'])
        
        for alumni in queryset:
            writer.writerow([
                alumni.full_name,
                alumni.email,
                alumni.batch.batch_year_range if alumni.batch else '',
                alumni.employment_status
            ])
        return response
    
    @action(detail=False, methods=['get'])
    def stats(self, request):
        """Alumni statistics"""
        queryset = self.get_queryset()
        total = queryset.count()
        employed = queryset.filter(employment_status='employed').count()
        
        return Response({
            'total_alumni': total,
            'employed_count': employed,
            'employment_rate': round((employed / total * 100) if total > 0 else 0, 2)
        })
    
    @action(detail=False, methods=['get'])
    def batch_stats(self, request):
        """Batch statistics"""
        batches = AlumniBatch.objects.all()
        for batch in batches:
            batch.update_statistics()
        
        return Response({
            'total_batches': batches.count(),
            'batches': AlumniBatchListSerializer(batches, many=True).data
        })


class AlumniBatchViewSet(viewsets.ModelViewSet):
    """ViewSet for Alumni Batch management"""
    
    queryset = AlumniBatch.objects.all()
    serializer_class = AlumniBatchSerializer
    permission_classes = [IsPeopleTeamOrReadOnly]
    ordering = ['-batch_year_range']
    
    def perform_create(self, serializer):
        batch = serializer.save()
        batch.update_statistics()
    
    def perform_update(self, serializer):
        batch = serializer.save()
        batch.update_statistics()
    
    @action(detail=True, methods=['post'])
    def update_stats(self, request, pk=None):
        """Manually update batch statistics"""
        batch = self.get_object()
        batch.update_statistics()
        serializer = self.get_serializer(batch)
        return Response({
            'message': 'Statistics updated successfully',
            'batch': serializer.data
        })
