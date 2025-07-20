from rest_framework import serializers
from .models import GalleryCategory, GalleryImage, GalleryAlbum


class GalleryCategorySerializer(serializers.ModelSerializer):
    """Serializer for gallery categories"""
    album_count = serializers.ReadOnlyField()
    total_images = serializers.ReadOnlyField()
    
    class Meta:
        model = GalleryCategory
        fields = [
            'id', 'name', 'category_type', 'description', 'slug', 'icon',
            'is_active', 'display_order', 'album_count', 'total_images',
            'created_at', 'updated_at'
        ]


class GalleryAlbumSerializer(serializers.ModelSerializer):
    """Serializer for gallery albums"""
    category_name = serializers.CharField(source='category.name', read_only=True)
    image_count = serializers.ReadOnlyField()
    
    class Meta:
        model = GalleryAlbum
        fields = [
            'id', 'name', 'description', 'slug', 'category', 'category_name',
            'cover_image', 'event_date', 'location', 'is_active', 'is_public',
            'is_featured', 'display_order', 'image_count', 'created_by',
            'created_at', 'updated_at'
        ]


class GalleryImageSerializer(serializers.ModelSerializer):
    """Serializer for gallery images"""
    album_name = serializers.CharField(source='album.name', read_only=True)
    category_name = serializers.CharField(source='album.category.name', read_only=True)
    category_type = serializers.CharField(source='album.category.category_type', read_only=True)
    file_size_mb = serializers.ReadOnlyField()
    tag_list = serializers.ReadOnlyField()
    
    class Meta:
        model = GalleryImage
        fields = [
            'id', 'title', 'description', 'image', 'thumbnail', 'album', 'album_name',
            'category_name', 'category_type', 'tags', 'tag_list', 'photographer',
            'camera_info', 'is_featured', 'is_public', 'display_order',
            'uploaded_by', 'file_size', 'file_size_mb', 'image_width', 'image_height',
            'created_at', 'updated_at'
        ]
        read_only_fields = ['uploaded_by', 'file_size', 'image_width', 'image_height']


class GalleryImageCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating gallery images"""
    
    class Meta:
        model = GalleryImage
        fields = [
            'title', 'description', 'image', 'album', 'tags', 'photographer',
            'camera_info', 'is_featured', 'is_public', 'display_order'
        ]
    
    def create(self, validated_data):
        # Set uploaded_by to current user
        validated_data['uploaded_by'] = self.context['request'].user
        return super().create(validated_data)


class GalleryAlbumCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating gallery albums"""
    
    class Meta:
        model = GalleryAlbum
        fields = [
            'name', 'description', 'slug', 'category', 'cover_image',
            'event_date', 'location', 'is_active', 'is_public', 'is_featured', 'display_order'
        ]
    
    def create(self, validated_data):
        # Set created_by to current user
        validated_data['created_by'] = self.context['request'].user
        return super().create(validated_data)
