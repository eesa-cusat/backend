from rest_framework import viewsets, permissions, status
from rest_framework.decorators import action
from rest_framework.response import Response
from django_filters import rest_framework as filters
from django.db.models import Q, Count
from django.shortcuts import get_object_or_404

from .models import GalleryCategory, GalleryImage, GalleryAlbum
from .serializers import (
    GalleryCategorySerializer,
    GalleryAlbumSerializer,
    GalleryImageSerializer,
    GalleryImageCreateSerializer,
    GalleryAlbumCreateSerializer,
)


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
        return queryset.select_related('category', 'created_by')
    
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
    def featured(self, request):
        """Get featured images"""
        images = self.get_queryset().filter(is_featured=True)
        serializer = self.get_serializer(images, many=True)
        return Response(serializer.data)
    
    @action(detail=False, methods=['get'])
    def by_category(self, request):
        """Get images grouped by category"""
        categories = GalleryCategory.objects.filter(is_active=True)
        result = []
        
        for category in categories:
            images = self.get_queryset().filter(
                album__category=category,
                is_public=True
            )[:10]  # Limit to 10 images per category
            
            serializer = self.get_serializer(images, many=True)
            result.append({
                'category': GalleryCategorySerializer(category).data,
                'images': serializer.data
            })
        
        return Response(result)
    
    @action(detail=False, methods=['get'])
    def recent(self, request):
        """Get recent images"""
        images = self.get_queryset().filter(is_public=True)[:20]
        serializer = self.get_serializer(images, many=True)
        return Response(serializer.data)
