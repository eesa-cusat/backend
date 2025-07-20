from django.urls import path
from . import views

urlpatterns = [
    path('', views.projects_list, name='projects_list'),
    path('<int:pk>/', views.project_detail, name='project_detail'),
    path('create/', views.create_project, name='create_project'),
    path('<int:pk>/update/', views.update_project, name='update_project'),
    path('<int:pk>/delete/', views.delete_project, name='delete_project'),
    path('my/', views.my_projects, name='my_projects'),
    path('featured/', views.featured_projects, name='featured_projects'),
]
