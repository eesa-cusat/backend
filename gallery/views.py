from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action, api_view, permission_classes
from rest_framework.response import Response
from django_filters import rest_framework as filters
from django.db.models import Q, Count, Prefetch
from django.shortcuts import get_object_or_404
from django.core.cache import cache
from performance_optimizations import cache_response, smart_pagination

from .models import GalleryCategory, GalleryImage, GalleryAlbum
from .serializers import (
    GalleryCategorySerializer,
    GalleryAlbumSerializer,
    GalleryImageSerializer,
    GalleryImageCreateSerializer,
    GalleryAlbumCreateSerializer,
)


@api_view(['GET'])
@permission_classes([permissions.AllowAny])
@cache_response(timeout=1800, key_prefix='gallery_batch')  # Cache for 30 minutes
def gallery_batch_data(request):
    """Optimized batch endpoint for gallery page - loads everything at once"""
    category_id = request.GET.get('category')
    album_id = request.GET.get('album')
    
    # Get categories with album count
    categories = GalleryCategory.objects.filter(is_active=True).annotate(
        album_count=Count('albums', filter=Q(albums__is_active=True, albums__is_public=True))
    ).only('id', 'name', 'category_type', 'display_order').order_by('display_order')
    
    # Base queryset for albums
    albums_queryset = GalleryAlbum.objects.filter(
        is_active=True, is_public=True
    ).select_related('category').prefetch_related(
        Prefetch('images', queryset=GalleryImage.objects.filter(
            is_public=True, is_featured=True
        ).only('id', 'image', 'title', 'album_id'))
    ).only(
        'id', 'name', 'description', 'event_date', 'display_order', 
        'is_featured', 'cover_image', 'category__name'
    )
    
    if category_id:
        albums_queryset = albums_queryset.filter(category_id=category_id)
    
    albums = albums_queryset.order_by('-is_featured', '-display_order', '-created_at')
    
    # Get featured images
    featured_images = GalleryImage.objects.filter(
        is_public=True, is_featured=True
    ).select_related('album', 'album__category').only(
        'id', 'title', 'image', 'display_order', 'album__name', 'album__category__name'
    ).order_by('-display_order', '-created_at')[:12]
    
    # Get recent images if no filters
    recent_images = []
    if not category_id and not album_id:
        recent_images = GalleryImage.objects.filter(
            is_public=True
        ).select_related('album').only(
            'id', 'title', 'image', 'created_at', 'album__name'
        ).order_by('-created_at')[:20]
    
    # Get images for specific album
    album_images = []
    if album_id:
        album_images = GalleryImage.objects.filter(
            album_id=album_id, is_public=True
        ).only(
            'id', 'title', 'image', 'description', 'display_order'
        ).order_by('-display_order', '-created_at')
    
    return Response({
        'categories': GalleryCategorySerializer(categories, many=True).data,
        'albums': GalleryAlbumSerializer(albums, many=True).data,
        'featured_images': GalleryImageSerializer(featured_images, many=True).data,
        'recent_images': GalleryImageSerializer(recent_images, many=True).data,
        'album_images': GalleryImageSerializer(album_images, many=True).data,
        'filters': {
            'category': category_id,
            'album': album_id
        }
    })


class GalleryCategoryViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for gallery categories"""
    queryset = GalleryCategory.objects.filter(is_active=True)
    serializer_class = GalleryCategorySerializer
    permission_classes = [permissions.AllowAny]
    filterset_fields = ['category_type', 'is_active']
    search_fields = ['name', 'description']
    ordering_fields = ['name', 'display_order', 'created_at']
    ordering = ['display_order', 'name']
    
    @action(detail=True, methods=['get'])
    def albums(self, request, pk=None):
        """Get albums for a specific category"""
        category = self.get_object()
        albums = GalleryAlbum.objects.filter(
            category=category, 
            is_active=True, 
            is_public=True
        ).select_related('category')
        
        serializer = GalleryAlbumSerializer(albums, many=True)
        return Response(serializer.data)


class GalleryAlbumViewSet(viewsets.ModelViewSet):
    """ViewSet for gallery albums"""
    queryset = GalleryAlbum.objects.filter(is_active=True)
    serializer_class = GalleryAlbumSerializer
    permission_classes = [permissions.AllowAny]
    filterset_fields = ['category', 'is_public', 'is_featured']
    search_fields = ['name', 'description', 'location']
    ordering_fields = ['name', 'event_date', 'display_order', 'created_at']
    ordering = ['-is_featured', '-display_order', '-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by public albums for non-authenticated users
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(is_public=True)
        return queryset.select_related('category', 'created_by').prefetch_related(
            Prefetch('images', queryset=GalleryImage.objects.filter(is_featured=True))
        )
    
    def get_serializer_class(self):
        if self.action == 'create':
            return GalleryAlbumCreateSerializer
        return GalleryAlbumSerializer
    
    @action(detail=True, methods=['get'])
    def images(self, request, pk=None):
        """Get images for a specific album"""
        album = self.get_object()
        images = GalleryImage.objects.filter(
            album=album, 
            is_public=True
        ).select_related('album', 'album__category')
        
        serializer = GalleryImageSerializer(images, many=True)
        return Response(serializer.data)


class GalleryImageFilter(filters.FilterSet):
    """Filter for gallery images"""
    category = filters.NumberFilter(field_name='album__category', lookup_expr='exact')
    category_type = filters.CharFilter(field_name='album__category__category_type', lookup_expr='exact')
    album = filters.NumberFilter(field_name='album', lookup_expr='exact')
    event_date = filters.DateFilter(field_name='album__event_date', lookup_expr='exact')
    event_date_range = filters.DateFromToRangeFilter(field_name='album__event_date')
    
    class Meta:
        model = GalleryImage
        fields = {
            'is_featured': ['exact'],
            'is_public': ['exact'],
            'photographer': ['icontains'],
            'tags': ['icontains'],
            'created_at': ['gte', 'lte'],
        }


class GalleryImageViewSet(viewsets.ModelViewSet):
    """ViewSet for gallery images"""
    queryset = GalleryImage.objects.all()
    serializer_class = GalleryImageSerializer
    permission_classes = [permissions.AllowAny]
    filterset_class = GalleryImageFilter
    search_fields = ['title', 'description', 'album__name', 'tags', 'photographer']
    ordering_fields = ['title', 'display_order', 'created_at']
    ordering = ['-is_featured', '-display_order', '-created_at']
    
    def get_queryset(self):
        queryset = super().get_queryset()
        # Filter by public images for non-authenticated users
        if not self.request.user.is_authenticated:
            queryset = queryset.filter(is_public=True)
        return queryset.select_related('album', 'album__category', 'uploaded_by')
    
    def get_serializer_class(self):
        if self.action == 'create':
            return GalleryImageCreateSerializer
        return GalleryImageSerializer
    
    @action(detail=False, methods=['get'])
    @cache_response(timeout=3600, key_prefix='gallery_featured')
    def featured(self, request):
        """Get featured images"""
        images = self.get_queryset().filter(is_featured=True).select_related('album', 'album__category')
        serializer = self.get_serializer(images, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    @cache_response(timeout=1800, key_prefix='gallery_by_category')
    def by_category(self, request):
        """Get images grouped by category"""
        categories = GalleryCategory.objects.filter(is_active=True).prefetch_related(
            Prefetch('albums__images', queryset=GalleryImage.objects.filter(
                is_public=True
            ).select_related('album').order_by('-created_at')[:10])
        )
        result = []
        
        for category in categories:
            # Get images from all albums in this category
            images = GalleryImage.objects.filter(
                album__category=category,
                is_public=True
            ).select_related('album')[:10]
            
            serializer = self.get_serializer(images, many=True)
            result.append({
                'category': GalleryCategorySerializer(category).data,
                'images': serializer.data
            })
        
        return Response(result)
    
    @action(detail=False, methods=['get'])
    @cache_response(timeout=900, key_prefix='gallery_recent')
    def recent(self, request):
        """Get recent images"""
        images = self.get_queryset().filter(is_public=True).select_related('album', 'album__category')[:20]
        serializer = self.get_serializer(images, many=True)
        return Response(serializer.data)
