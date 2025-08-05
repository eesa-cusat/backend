from rest_framework import serializers
from .models import TeamMember

class TeamMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamMember
        fields = ['id', 'name', 'position', 'team_type', 'bio', 'image', 'email', 'linkedin_url', 'github_url', 'is_active', 'order'] 