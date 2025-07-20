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

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def job_opportunities_list(request):
    """List all active job opportunities with optional filtering"""
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

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def internship_opportunities_list(request):
    """List all active internship opportunities with optional filtering"""
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
            Q(description__icontains=search) |
            Q(skills__icontains=search)
        )
    
    serializer = InternshipOpportunitySerializer(internships, many=True)
    
    return Response({
        'internships': serializer.data,
        'durations': dict(InternshipOpportunity.DURATION_CHOICES),
        'internship_types': dict(InternshipOpportunity.INTERNSHIP_TYPES),
        'count': internships.count()
    })

@api_view(['GET'])
@permission_classes([permissions.AllowAny])
def certificate_opportunities_list(request):
    """List all active certificate opportunities with optional filtering"""
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
            Q(description__icontains=search) |
            Q(skills_covered__icontains=search)
        )
    
    serializer = CertificateOpportunitySerializer(certificates, many=True)
    
    return Response({
        'certificates': serializer.data,
        'providers': dict(CertificateOpportunity.PROVIDERS),
        'certificate_types': dict(CertificateOpportunity.CERTIFICATE_TYPES),
        'count': certificates.count()
    })

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_job_opportunity(request):
    """Create a new job opportunity (only for teachers, alumni, tech_heads, admins)"""
    if request.user.role not in ['teacher', 'alumni', 'tech_head', 'admin']:
        return Response(
            {'error': 'You do not have permission to post job opportunities'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer = JobOpportunityCreateSerializer(data=request.data)
    if serializer.is_valid():
        job_opportunity = serializer.save(posted_by=request.user)
        response_serializer = JobOpportunitySerializer(job_opportunity)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_internship_opportunity(request):
    """Create a new internship opportunity"""
    if request.user.role not in ['teacher', 'alumni', 'tech_head', 'admin']:
        return Response(
            {'error': 'You do not have permission to post internship opportunities'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer = InternshipOpportunityCreateSerializer(data=request.data)
    if serializer.is_valid():
        internship = serializer.save(posted_by=request.user)
        response_serializer = InternshipOpportunitySerializer(internship)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['POST'])
@permission_classes([permissions.IsAuthenticated])
def create_certificate_opportunity(request):
    """Create a new certificate opportunity"""
    if request.user.role not in ['teacher', 'alumni', 'tech_head', 'admin']:
        return Response(
            {'error': 'You do not have permission to post certificate opportunities'}, 
            status=status.HTTP_403_FORBIDDEN
        )
    
    serializer = CertificateOpportunityCreateSerializer(data=request.data)
    if serializer.is_valid():
        certificate = serializer.save(posted_by=request.user)
        response_serializer = CertificateOpportunitySerializer(certificate)
        return Response(response_serializer.data, status=status.HTTP_201_CREATED)
    
    return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

@api_view(['GET'])
@permission_classes([permissions.IsAuthenticated])
def job_opportunity_detail(request, pk):
    """Get detailed view of a job opportunity"""
    try:
        opportunity = JobOpportunity.objects.get(pk=pk, is_active=True)
        serializer = JobOpportunitySerializer(opportunity)
        return Response(serializer.data)
    except JobOpportunity.DoesNotExist:
        return Response(
            {'error': 'Job opportunity not found'}, 
            status=status.HTTP_404_NOT_FOUND
        )
