from django.urls import path
from . import views

app_name = 'careers'

urlpatterns = [
    # Job opportunities
    path('opportunities/', views.job_opportunities_list, name='opportunities-list'),
    path('opportunities/create/', views.create_job_opportunity, name='create-opportunity'),
    path('opportunities/<int:pk>/', views.job_opportunity_detail, name='opportunity-detail'),
    
    # Internship opportunities
    path('internships/', views.internship_opportunities_list, name='internships-list'),
    path('internships/create/', views.create_internship_opportunity, name='create-internship'),
    
    # Certificate opportunities
    path('certificates/', views.certificate_opportunities_list, name='certificates-list'),
    path('certificates/create/', views.create_certificate_opportunity, name='create-certificate'),
]
