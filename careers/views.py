from rest_framework import generics, permissions, status
from rest_framework.decorators import api_view, permission_classes
from rest_framework.response import Response
from django.db.models import Q
from .models import JobOpportunity, InternshipOpportunity, CertificateOpportunity
from .serializers import (
    JobOpportunitySerializer, JobOpportunityCreateSerializer,
    InternshipOpportunitySerializer, InternshipOpportunityCreateSerializer,
    CertificateOpportunitySerializer, CertificateOpportunityCreateSerializer
)
from accounts.permissions import IsCareersTeamOrReadOnly
from utils.redis_cache import CareersCache, get_or_set_cache, CacheTTL

@api_view(['GET', 'POST'])
@permission_classes([permissions.AllowAny])
def job_opportunities_list(request):
    """List all active job opportunities with optional filtering (GET) or create new job (POST)"""
    if request.method == 'GET':
        opportunities = JobOpportunity.objects.filter(is_active=True)
        
        # Optional filtering
        job_type = request.query_params.get('job_type')
        experience_level = request.query_params.get('experience_level')
        location = request.query_params.get('location')
        search = request.query_params.get('search')
        
        if job_type:
            opportunities = opportunities.filter(job_type=job_type)
        
        if experience_level:
            opportunities = opportunities.filter(experience_level=experience_level)
        
        if location:
            opportunities = opportunities.filter(location__icontains=location)
        
        if search:
            opportunities = opportunities.filter(
                Q(title__icontains=search) |
                Q(company__icontains=search) |
                Q(description__icontains=search)
            )
        
        opportunities = opportunities.order_by('-created_at')
        serializer = JobOpportunitySerializer(opportunities, many=True)
        return Response({
            'count': opportunities.count(),
            'results': serializer.data
        })
    
    elif request.method == 'POST':
        # Check permissions for POST
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        
        if not request.user.is_superuser and not request.user.groups.filter(name='careers_team').exists():
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = JobOpportunityCreateSerializer(data=request.data)
        if serializer.is_valid():
            opportunity = serializer.save(created_by=request.user)
            return Response({
                'id': opportunity.id,
                'title': opportunity.title,
                'message': 'Job opportunity created successfully'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        opportunities = opportunities.filter(location__icontains=location)
    
    if search:
        opportunities = opportunities.filter(
            Q(title__icontains=search) |
            Q(company__icontains=search) |
            Q(description__icontains=search) |
            Q(skills__icontains=search)
        )
    
    serializer = JobOpportunitySerializer(opportunities, many=True)
    
    # Also return available filter options
    job_types = JobOpportunity.JOB_TYPES
    experience_levels = JobOpportunity.EXPERIENCE_LEVELS
    
    return Response({
        'opportunities': serializer.data,
        'job_types': dict(job_types),
        'experience_levels': dict(experience_levels),
        'count': opportunities.count()
    })

@api_view(['GET', 'POST'])
@permission_classes([permissions.AllowAny])
def internship_opportunities_list(request):
    """List all active internship opportunities with optional filtering (GET) or create new internship (POST)"""
    if request.method == 'GET':
        internships = InternshipOpportunity.objects.filter(is_active=True)
        
        # Optional filtering
        duration = request.query_params.get('duration')
        internship_type = request.query_params.get('internship_type')
        is_remote = request.query_params.get('is_remote')
        location = request.query_params.get('location')
        search = request.query_params.get('search')
        
        if duration:
            internships = internships.filter(duration=duration)
        
        if internship_type:
            internships = internships.filter(internship_type=internship_type)
        
        if is_remote and is_remote.lower() == 'true':
            internships = internships.filter(is_remote=True)
        
        if location:
            internships = internships.filter(location__icontains=location)
        
        if search:
            internships = internships.filter(
                Q(title__icontains=search) |
                Q(company__icontains=search) |
                Q(description__icontains=search)
            )
        
        internships = internships.order_by('-created_at')
        serializer = InternshipOpportunitySerializer(internships, many=True)
        return Response({
            'count': internships.count(),
            'results': serializer.data
        })
    
    elif request.method == 'POST':
        # Check permissions for POST
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        
        if not request.user.is_superuser and not request.user.groups.filter(name='careers_team').exists():
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = InternshipOpportunityCreateSerializer(data=request.data)
        if serializer.is_valid():
            internship = serializer.save(created_by=request.user)
            return Response({
                'id': internship.id,
                'title': internship.title,
                'message': 'Internship opportunity created successfully'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([permissions.AllowAny])
def internship_opportunity_detail(request, pk):
    """Get, update, or delete detailed view of an internship opportunity"""
    try:
        internship = InternshipOpportunity.objects.get(pk=pk)
        
        # For GET requests, only show active opportunities to public
        if request.method == 'GET' and not internship.is_active:
            if not request.user.is_authenticated or (not request.user.is_superuser and not request.user.groups.filter(name='careers_team').exists()):
                return Response({'error': 'Internship opportunity not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if request.method == 'GET':
            serializer = InternshipOpportunitySerializer(internship)
            return Response(serializer.data)
        
        elif request.method in ['PUT', 'DELETE']:
            # Check permissions for PUT/DELETE
            if not request.user.is_authenticated:
                return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
            
            if not request.user.is_superuser and not request.user.groups.filter(name='careers_team').exists():
                return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
            
            if request.method == 'PUT':
                serializer = InternshipOpportunityCreateSerializer(internship, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response({
                        'id': internship.id,
                        'title': internship.title,
                        'message': 'Internship opportunity updated successfully'
                    })
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            elif request.method == 'DELETE':
                internship.delete()
                return Response({'message': 'Internship opportunity deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
                
    except InternshipOpportunity.DoesNotExist:
        return Response(
            {'error': 'Internship opportunity not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['GET', 'POST'])
@permission_classes([permissions.AllowAny])
def certificate_opportunities_list(request):
    """List all active certificate opportunities with optional filtering (GET) or create new certificate (POST)"""
    if request.method == 'GET':
        certificates = CertificateOpportunity.objects.filter(is_active=True)
        
        # Optional filtering
        provider = request.query_params.get('provider')
        certificate_type = request.query_params.get('certificate_type')
        is_free = request.query_params.get('is_free')
        industry_recognized = request.query_params.get('industry_recognized')
        search = request.query_params.get('search')
        
        if provider:
            certificates = certificates.filter(provider=provider)
        
        if certificate_type:
            certificates = certificates.filter(certificate_type=certificate_type)
        
        if is_free and is_free.lower() == 'true':
            certificates = certificates.filter(is_free=True)
        
        if industry_recognized and industry_recognized.lower() == 'true':
            certificates = certificates.filter(industry_recognized=True)
        
        if search:
            certificates = certificates.filter(
                Q(title__icontains=search) |
                Q(provider__icontains=search) |
                Q(description__icontains=search)
            )
        
        certificates = certificates.order_by('-created_at')
        serializer = CertificateOpportunitySerializer(certificates, many=True)
        return Response({
            'count': certificates.count(),
            'results': serializer.data
        })
    
    elif request.method == 'POST':
        # Check permissions for POST
        if not request.user.is_authenticated:
            return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
        
        if not request.user.is_superuser and not request.user.groups.filter(name='careers_team').exists():
            return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
        
        serializer = CertificateOpportunityCreateSerializer(data=request.data)
        if serializer.is_valid():
            certificate = serializer.save(created_by=request.user)
            return Response({
                'id': certificate.id,
                'title': certificate.title,
                'message': 'Certificate opportunity created successfully'
            }, status=status.HTTP_201_CREATED)
        return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)


@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([permissions.AllowAny])
def certificate_opportunity_detail(request, pk):
    """Get, update, or delete detailed view of a certificate opportunity"""
    try:
        certificate = CertificateOpportunity.objects.get(pk=pk)
        
        # For GET requests, only show active opportunities to public
        if request.method == 'GET' and not certificate.is_active:
            if not request.user.is_authenticated or (not request.user.is_superuser and not request.user.groups.filter(name='careers_team').exists()):
                return Response({'error': 'Certificate opportunity not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if request.method == 'GET':
            serializer = CertificateOpportunitySerializer(certificate)
            return Response(serializer.data)
        
        elif request.method in ['PUT', 'DELETE']:
            # Check permissions for PUT/DELETE
            if not request.user.is_authenticated:
                return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
            
            if not request.user.is_superuser and not request.user.groups.filter(name='careers_team').exists():
                return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
            
            if request.method == 'PUT':
                serializer = CertificateOpportunityCreateSerializer(certificate, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response({
                        'id': certificate.id,
                        'title': certificate.title,
                        'message': 'Certificate opportunity updated successfully'
                    })
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            elif request.method == 'DELETE':
                certificate.delete()
                return Response({'message': 'Certificate opportunity deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
                
    except CertificateOpportunity.DoesNotExist:
        return Response(
            {'error': 'Certificate opportunity not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )

@api_view(['POST'])
@permission_classes([IsCareersTeamOrReadOnly])
def create_job_opportunity(request):
    """Create a new job opportunity (careers team only)"""
    serializer = JobOpportunityCreateSerializer(data=request.data)
    if serializer.is_valid():
        job_opportunity = serializer.save(posted_by=request.user)
        response_serializer = JobOpportunitySerializer(job_opportunity)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsCareersTeamOrReadOnly])
def create_internship_opportunity(request):
    """Create a new internship opportunity (careers team only)"""
    serializer = InternshipOpportunityCreateSerializer(data=request.data)
    if serializer.is_valid():
        internship = serializer.save(posted_by=request.user)
        response_serializer = InternshipOpportunitySerializer(internship)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([IsCareersTeamOrReadOnly])
def create_certificate_opportunity(request):
    """Create a new certificate opportunity (careers team only)"""
    serializer = CertificateOpportunityCreateSerializer(data=request.data)
    if serializer.is_valid():
        certificate = serializer.save(posted_by=request.user)
        response_serializer = CertificateOpportunitySerializer(certificate)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET', 'PUT', 'DELETE'])
@permission_classes([permissions.AllowAny])
def job_opportunity_detail(request, pk):
    """Get, update, or delete detailed view of a job opportunity"""
    try:
        opportunity = JobOpportunity.objects.get(pk=pk)
        
        # For GET requests, only show active opportunities to public
        if request.method == 'GET' and not opportunity.is_active:
            if not request.user.is_authenticated or (not request.user.is_superuser and not request.user.groups.filter(name='careers_team').exists()):
                return Response({'error': 'Job opportunity not found'}, status=status.HTTP_404_NOT_FOUND)
        
        if request.method == 'GET':
            serializer = JobOpportunitySerializer(opportunity)
            return Response(serializer.data)
        
        elif request.method in ['PUT', 'DELETE']:
            # Check permissions for PUT/DELETE
            if not request.user.is_authenticated:
                return Response({'error': 'Authentication required'}, status=status.HTTP_401_UNAUTHORIZED)
            
            if not request.user.is_superuser and not request.user.groups.filter(name='careers_team').exists():
                return Response({'error': 'Permission denied'}, status=status.HTTP_403_FORBIDDEN)
            
            if request.method == 'PUT':
                serializer = JobOpportunityCreateSerializer(opportunity, data=request.data, partial=True)
                if serializer.is_valid():
                    serializer.save()
                    return Response({
                        'id': opportunity.id,
                        'title': opportunity.title,
                        'message': 'Job opportunity updated successfully'
                    })
                return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
            
            elif request.method == 'DELETE':
                opportunity.delete()
                return Response({'message': 'Job opportunity deleted successfully'}, status=status.HTTP_204_NO_CONTENT)
                
    except JobOpportunity.DoesNotExist:
        return Response(
            {'error': 'Job opportunity not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
