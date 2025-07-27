from django.urls import path
from . import views

urlpatterns = [
    # Scheme endpoints
    path('schemes/', views.schemes_list, name='schemes_list'),
    path('schemes/create/', views.create_scheme, name='create_scheme'),
    
    # Subject endpoints
    path('subjects/', views.subjects_by_scheme_semester, name='subjects_by_scheme_semester'),
    path('subjects/create/', views.create_subject, name='create_subject'),
    
    # Academic Categories endpoints
    path('categories/', views.academic_categories_list, name='academic_categories_list'),
    path('categories/<str:category_type>/', views.category_detail, name='category_detail'),
    
    # Academic Resources endpoints
    path('resources/', views.academic_resources_list, name='academic_resources_list'),
    path('resources/<int:pk>/', views.academic_resource_detail, name='academic_resource_detail'),
    path('resources/<int:pk>/download/', views.download_academic_resource, name='download_academic_resource'),
    path('resources/upload/', views.upload_academic_resource, name='upload_academic_resource'),
    path('resources/<int:pk>/like/', views.toggle_resource_like, name='toggle_resource_like'),
    
    # Unverified notes (staff only)
    path('unverified-notes/', views.unverified_notes, name='unverified_notes'),
    path('approve-note/<int:pk>/', views.approve_note, name='approve_note'),
]
