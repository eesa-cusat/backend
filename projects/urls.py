from django.urls import path, include
from rest_framework.routers import DefaultRouter
from . import views

# Create router for ViewSets
router = DefaultRouter()
router.register(r'images', views.ProjectImageViewSet)
router.register(r'videos', views.ProjectVideoViewSet)

urlpatterns = [
    # Optimized batch endpoint
    path('batch-data/', views.projects_batch_data, name='projects_batch_data'),
    
    # Function-based views
    path('', views.projects_list, name='projects_list'),
    path('<int:pk>/', views.project_detail, name='project_detail'),
    path('<int:pk>/report/', views.project_report, name='project_report'),  # New report endpoint
    path('create/', views.create_project, name='create_project'),
    path('<int:pk>/update/', views.update_project, name='update_project'),
    path('<int:pk>/delete/', views.delete_project, name='delete_project'),
    path('my/', views.my_projects, name='my_projects'),
    path('featured/', views.featured_projects, name='featured_projects'),
    
    # ViewSet-based views for images and videos
    path('', include(router.urls)),
]
