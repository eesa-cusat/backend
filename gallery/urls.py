from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router and register viewsets
router = DefaultRouter()
router.register(r'albums', views.AlbumViewSet, basename='album')
router.register(r'photos', views.PhotoViewSet, basename='photo')

app_name = 'gallery'

urlpatterns = [
    path('', include(router.urls)),
]
