from django.urls import path
from . import views

app_name = 'careers'

urlpatterns = [
    # Job opportunities
    path('opportunities/', views.job_opportunities_list, name='opportunities-list'),
    path('opportunities/<int:pk>/', views.job_opportunity_detail, name='opportunity-detail'),
    
    # Internship opportunities
    path('internships/', views.internship_opportunities_list, name='internships-list'),
    path('internships/<int:pk>/', views.internship_opportunity_detail, name='internship-detail'),
    
    # Certificate opportunities
    path('certificates/', views.certificate_opportunities_list, name='certificates-list'),
    path('certificates/<int:pk>/', views.certificate_opportunity_detail, name='certificate-detail'),
]
