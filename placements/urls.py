from django.urls import path
from . import views

urlpatterns = [
    # Company endpoints
    path('companies/', views.companies_list, name='companies_list'),
    path('companies/<int:pk>/', views.company_detail, name='company_detail'),
    
    # Placement drive endpoints
    path('drives/', views.placement_drives_list, name='placement_drives_list'),
    path('drives/<int:pk>/', views.placement_drive_detail, name='placement_drive_detail'),
    
    # Application endpoints
    path('applications/', views.placement_applications_list, name='placement_applications_list'),
    path('applications/<int:pk>/', views.placement_application_detail, name='placement_application_detail'),
    
    # Placed students endpoints
    path('placed-students/', views.placed_students_list, name='placed_students_list'),
    path('placed-students/<int:pk>/', views.placed_student_detail, name='placed_student_detail'),
    path('placed-students/create/', views.placed_student_create, name='placed_student_create'),
    
    # Statistics endpoints
    path('statistics/', views.placement_statistics, name='placement_statistics'),
    path('overview/', views.placement_overview, name='placement_overview'),
    
    # Filter options endpoint
    path('filters/', views.placement_filters, name='placement_filters'),
    
    # Additional placement endpoints
    path('statistics-detailed/', views.placement_statistics_detailed, name='placement_statistics_detailed'),
    path('past-recruiters/', views.past_recruiters, name='past_recruiters'),
]
