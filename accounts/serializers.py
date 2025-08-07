from rest_framework import serializers
from django.contrib.auth import authenticate
from .models import TeamMember, User


class TeamMemberSerializer(serializers.ModelSerializer):
    class Meta:
        model = TeamMember
        fields = ['id', 'name', 'position', 'team_type', 'bio', 'image', 'email', 'linkedin_url', 'github_url', 'is_active', 'order']


class UserProfileSerializer(serializers.ModelSerializer):
    """Serializer for user profile information"""
    groups = serializers.StringRelatedField(many=True, read_only=True)
    
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name', 'groups', 'is_staff', 'is_superuser']
        read_only_fields = ['id', 'username', 'groups', 'is_staff', 'is_superuser']


class LoginSerializer(serializers.Serializer):
    """Serializer for user login"""
    username = serializers.CharField()
    password = serializers.CharField(write_only=True)
    
    def validate(self, attrs):
        username = attrs.get('username')
        password = attrs.get('password')
        
        if username and password:
            user = authenticate(username=username, password=password)
            if user:
                if user.is_active:
                    attrs['user'] = user
                    return attrs
                else:
                    raise serializers.ValidationError('User account is disabled.')
            else:
                raise serializers.ValidationError('Unable to login with provided credentials.')
        else:
            raise serializers.ValidationError('Must include username and password.')


class TeamMemberAdminSerializer(serializers.ModelSerializer):
    """Serializer for admin team member operations"""
    
    class Meta:
        model = TeamMember
        fields = [
            'id', 'name', 'position', 'team_type', 'bio', 'image', 
            'email', 'linkedin_url', 'github_url', 'is_active', 'order'
        ] 