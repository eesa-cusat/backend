from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    TeamMemberViewSet, 
    login_view, 
    logout_view, 
    me_view, 
    admin_stats,
    csrf_token_view
)

# API routes with DRF router
router = DefaultRouter()
router.register(r'team-members', TeamMemberViewSet, basename='team-member')

urlpatterns = [
    # Authentication endpoints
    path('auth/login/', login_view, name='admin-login'),
    path('auth/logout/', logout_view, name='admin-logout'),
    path('auth/me/', me_view, name='current-user'),
    path('auth/csrf/', csrf_token_view, name='csrf-token'),
    
    # Admin dashboard
    path('admin/stats/', admin_stats, name='admin-stats'),
    
    # DRF API endpoints
    path('', include(router.urls)),
]
