from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.pagination import PageNumberPagination
from django.db.models import Q
from .models import Album, Photo
from .serializers import AlbumSerializer, AlbumListSerializer, PhotoSerializer
from accounts.permissions import IsGalleryManager


class GalleryPageNumberPagination(PageNumberPagination):
    """Custom pagination for gallery endpoints"""
    page_size = 12
    page_size_query_param = 'page_size'
    max_page_size = 50


class PhotoPageNumberPagination(PageNumberPagination):
    """Custom pagination for photos - higher limit for gallery viewing"""
    page_size = 24
    page_size_query_param = 'page_size'
    max_page_size = 100


class AlbumViewSet(viewsets.ModelViewSet):
    """Gallery Albums management"""
    queryset = Album.objects.select_related('event', 'created_by').prefetch_related('photos').all()
    permission_classes = [IsGalleryManager]
    pagination_class = GalleryPageNumberPagination
    
    def get_serializer_class(self):
        if self.action == 'list':
            return AlbumListSerializer
        return AlbumSerializer
    
    def get_queryset(self):
        queryset = Album.objects.select_related('event', 'created_by').prefetch_related('photos').all()
        
        album_type = self.request.query_params.get('type')
        search_term = self.request.query_params.get('search', '').strip()
        
        if album_type in ['eesa', 'general', 'alumni']:
            queryset = queryset.filter(type=album_type)
        
        # Search functionality
        if search_term:
            queryset = queryset.filter(
                Q(name__icontains=search_term) |
                Q(description__icontains=search_term) |
                Q(event__title__icontains=search_term)
            )
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def public(self, request):
        """Public albums endpoint with pagination"""
        album_type = request.query_params.get('type')
        search_term = request.query_params.get('search', '').strip()
        
        queryset = Album.objects.select_related('event', 'created_by').prefetch_related('photos').all()
        
        if album_type in ['eesa', 'general', 'alumni']:
            queryset = queryset.filter(type=album_type)
            
        if search_term:
            queryset = queryset.filter(
                Q(name__icontains=search_term) |
                Q(description__icontains=search_term) |
                Q(event__title__icontains=search_term)
            )
        
        queryset = queryset.order_by('-created_at')
        
        # Apply pagination
        paginator = GalleryPageNumberPagination()
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = AlbumListSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = AlbumListSerializer(queryset, many=True)
        return Response(serializer.data)


class PhotoViewSet(viewsets.ModelViewSet):
    """Gallery Photos management"""
    queryset = Photo.objects.select_related('uploaded_by', 'album').all()
    serializer_class = PhotoSerializer
    permission_classes = [IsGalleryManager]
    pagination_class = PhotoPageNumberPagination
    
    def get_queryset(self):
        queryset = Photo.objects.select_related('uploaded_by', 'album').all()
        
        album_id = self.request.query_params.get('album')
        search_term = self.request.query_params.get('search', '').strip()
        
        if album_id:
            queryset = queryset.filter(album_id=album_id)
        
        if search_term:
            queryset = queryset.filter(
                Q(caption__icontains=search_term) |
                Q(uploaded_by__first_name__icontains=search_term) |
                Q(uploaded_by__last_name__icontains=search_term)
            )
        
        return queryset.order_by('-uploaded_at')
    
    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def public(self, request):
        """Public photos endpoint with pagination"""
        album_id = request.query_params.get('album')
        search_term = request.query_params.get('search', '').strip()
        
        queryset = Photo.objects.select_related('uploaded_by', 'album').all()
        
        if album_id:
            queryset = queryset.filter(album_id=album_id)
            
        if search_term:
            queryset = queryset.filter(
                Q(caption__icontains=search_term) |
                Q(uploaded_by__first_name__icontains=search_term) |
                Q(uploaded_by__last_name__icontains=search_term)
            )
        
        queryset = queryset.order_by('-uploaded_at')
        
        # Apply pagination
        paginator = PhotoPageNumberPagination()
        page = paginator.paginate_queryset(queryset, request)
        if page is not None:
            serializer = PhotoSerializer(page, many=True)
            return paginator.get_paginated_response(serializer.data)
        
        serializer = PhotoSerializer(queryset, many=True)
        return Response(serializer.data)
