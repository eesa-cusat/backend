from rest_framework import viewsets, permissions
from rest_framework.decorators import action
from rest_framework.response import Response
from .models import Album, Photo
from .serializers import AlbumSerializer, AlbumListSerializer, PhotoSerializer
from accounts.permissions import IsGalleryManager


class AlbumViewSet(viewsets.ModelViewSet):
    """Gallery Albums management"""
    queryset = Album.objects.all()
    permission_classes = [IsGalleryManager]
    
    def get_serializer_class(self):
        if self.action == 'list':
            return AlbumListSerializer
        return AlbumSerializer
    
    def get_queryset(self):
        queryset = Album.objects.all()
        
        album_type = self.request.query_params.get('type')
        if album_type in ['eesa', 'general']:
            queryset = queryset.filter(type=album_type)
        
        return queryset.order_by('-created_at')
    
    def perform_create(self, serializer):
        serializer.save(created_by=self.request.user)
    
    @action(detail=False, methods=['get'], permission_classes=[permissions.AllowAny])
    def public(self, request):
        """Public albums endpoint"""
        album_type = request.query_params.get('type')
        
        queryset = self.get_queryset()
        if album_type in ['eesa', 'general']:
            queryset = queryset.filter(type=album_type)
        
        serializer = AlbumSerializer(queryset, many=True)
        return Response(serializer.data)


class PhotoViewSet(viewsets.ModelViewSet):
    """Gallery Photos management"""
    queryset = Photo.objects.all()
    serializer_class = PhotoSerializer
    permission_classes = [IsGalleryManager]
    
    def get_queryset(self):
        queryset = Photo.objects.all()
        
        album_id = self.request.query_params.get('album')
        if album_id:
            queryset = queryset.filter(album_id=album_id)
        
        return queryset.order_by('-uploaded_at')
    
    def perform_create(self, serializer):
        serializer.save(uploaded_by=self.request.user)
