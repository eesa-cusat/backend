from django.urls import path
from . import views
from . import admin_views

urlpatterns = [
    # Scheme endpoints
    path('schemes/', views.schemes_list, name='schemes_list'),
    path('schemes/<int:pk>/', views.scheme_detail, name='scheme_detail'),
    
    # Subject endpoints
    path('subjects/', views.subjects_by_scheme_semester, name='subjects_by_scheme_semester'),
    path('subjects/<int:pk>/', views.subject_detail, name='subject_detail'),
    
    # Academic Categories endpoints
    path('categories/', views.academic_categories_list, name='academic_categories_list'),
    path('categories/<str:category_type>/', views.category_detail, name='category_detail'),
    
    # Academic Resources endpoints
    path('resources/', views.academic_resources_list, name='academic_resources_list'),
    path('resources/<int:pk>/', views.academic_resource_detail, name='academic_resource_detail'),
    path('resources/<int:pk>/download/', views.download_academic_resource, name='download_academic_resource'),
    path('resources/<int:pk>/like/', views.toggle_resource_like, name='toggle_resource_like'),
    
    # Unverified notes (academics team only)
    path('unverified-notes/', views.unverified_notes, name='unverified_notes'),
    path('approve-note/<int:pk>/', views.approve_note, name='approve_note'),
    path('toggle-approval/<int:pk>/', views.toggle_approval_status, name='toggle_approval_status'),
    
    # Admin endpoints for frontend admin panel
    path('admin/upload-multiple/', admin_views.upload_multiple_notes, name='admin_upload_multiple_notes'),
    path('admin/resources/', admin_views.admin_resources_list, name='admin_resources_list'),
    path('admin/resources/<int:pk>/', admin_views.update_resource, name='admin_update_resource'),
    path('admin/resources/<int:pk>/delete/', admin_views.delete_resource, name='admin_delete_resource'),
]
