from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import AlumniViewSet, AlumniBatchViewSet

router = DefaultRouter()
router.register(r'alumni', AlumniViewSet)
router.register(r'batches', AlumniBatchViewSet)

app_name = 'alumni'

urlpatterns = [
    path('', include(router.urls)),
    # Custom endpoints for entrepreneurship stats
    path('entrepreneurship-stats/', AlumniViewSet.as_view({'get': 'entrepreneurship_stats'}), name='entrepreneurship-stats'),
    path('entrepreneurs/', AlumniViewSet.as_view({'get': 'entrepreneurs'}), name='entrepreneurs'),
    path('startup-stories/', AlumniViewSet.as_view({'get': 'startup_stories'}), name='startup-stories'),
    
    # Batch-related endpoints
    path('batch-stats/', AlumniViewSet.as_view({'get': 'batch_stats'}), name='batch-stats'),
    path('create-batch-album/', AlumniViewSet.as_view({'post': 'create_batch_album'}), name='create-batch-album'),
]
