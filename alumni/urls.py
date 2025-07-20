from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AlumniViewSet

router = DefaultRouter()
router.register(r'alumni', AlumniViewSet)

app_name = 'alumni'

urlpatterns = [
    path('', include(router.urls)),
]
