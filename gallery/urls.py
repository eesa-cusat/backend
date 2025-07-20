from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

router = DefaultRouter()
router.register(r'categories', views.GalleryCategoryViewSet)
router.register(r'images', views.GalleryImageViewSet)
router.register(r'albums', views.GalleryAlbumViewSet)

urlpatterns = [
    path('', include(router.urls)),
]
