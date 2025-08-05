from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AlumniViewSet

router = DefaultRouter()
router.register(r'alumni', AlumniViewSet)

app_name = 'alumni'

urlpatterns = [
    path('', include(router.urls)),
    # Custom endpoints for entrepreneurship stats
    path('entrepreneurship-stats/', AlumniViewSet.as_view({'get': 'entrepreneurship_stats'}), name='entrepreneurship-stats'),
    path('entrepreneurs/', AlumniViewSet.as_view({'get': 'entrepreneurs'}), name='entrepreneurs'),
    path('startup-stories/', AlumniViewSet.as_view({'get': 'startup_stories'}), name='startup-stories'),
]
