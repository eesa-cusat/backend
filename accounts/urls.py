from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import TeamMemberViewSet

# Simple URLs for accounts app - focus on admin interface
router = DefaultRouter()
router.register(r'team-members', TeamMemberViewSet, basename='team-member')

urlpatterns = [
    # API endpoints for team members
    path('', include(router.urls)),
]
