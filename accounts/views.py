from rest_framework import viewsets
from .models import TeamMember
from .serializers import TeamMemberSerializer

class TeamMemberViewSet(viewsets.ReadOnlyModelViewSet):
    queryset = TeamMember.objects.filter(is_active=True).order_by('team_type', 'order', 'name')
    serializer_class = TeamMemberSerializer 