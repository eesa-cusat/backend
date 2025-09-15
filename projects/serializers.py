from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Project, TeamMember, ProjectImage, ProjectVideo

User = get_user_model()


class UserSerializer(serializers.ModelSerializer):
    """Simple user serializer for references"""
    class Meta:
        model = User
        fields = ['id', 'username', 'email', 'first_name', 'last_name']
        read_only_fields = ['id', 'username', 'email']


class TeamMemberSerializer(serializers.ModelSerializer):
    """Team member serializer"""
    
    class Meta:
        model = TeamMember
        fields = ['id', 'name', 'linkedin_url', 'role']
        read_only_fields = ['id']


class ProjectImageSerializer(serializers.ModelSerializer):
    """Project image serializer - first image acts as cover image"""
    
    class Meta:
        model = ProjectImage
        fields = ['id', 'project', 'image', 'caption', 'is_featured', 'created_at']
        read_only_fields = ['id', 'created_at']


class ProjectVideoSerializer(serializers.ModelSerializer):
    """Project video serializer"""
    
    class Meta:
        model = ProjectVideo
        fields = ['id', 'project', 'video_url', 'title', 'description', 'is_featured', 'created_at']
        read_only_fields = ['id', 'created_at']


class ProjectSerializer(serializers.ModelSerializer):
    """Detailed project serializer"""
    
    created_by = UserSerializer(read_only=True)
    team_members = TeamMemberSerializer(many=True, read_only=True)
    gallery_images = ProjectImageSerializer(many=True, read_only=True, source='images')
    videos = ProjectVideoSerializer(many=True, read_only=True)
    thumbnail_image = serializers.ImageField(read_only=True, source='project_images')
    featured_video = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = [
            'id', 'title', 'description', 'abstract', 'category', 'student_batch',
            'github_url', 'demo_url', 'project_report', 'created_by', 'team_members', 
            'thumbnail_image', 'gallery_images', 'videos', 'featured_video', 'created_at', 'updated_at'
        ]
        read_only_fields = ['id', 'created_by', 'created_at', 'updated_at']
    
    def get_featured_video(self, obj):
        """Get the featured video for this project"""
        featured_video = obj.videos.filter(is_featured=True).first()
        if featured_video:
            return ProjectVideoSerializer(featured_video).data
        return None


class ProjectCreateSerializer(serializers.ModelSerializer):
    """Serializer for creating projects"""
    
    team_members = TeamMemberSerializer(many=True, required=False)
    images = ProjectImageSerializer(many=True, required=False)
    videos = ProjectVideoSerializer(many=True, required=False)
    
    class Meta:
        model = Project
        fields = [
            'title', 'description', 'abstract', 'category', 'student_batch', 'github_url', 
            'demo_url', 'project_report', 'team_members', 'images', 'videos'
        ]
    
    def create(self, validated_data):
        team_members_data = validated_data.pop('team_members', [])
        images_data = validated_data.pop('images', [])
        videos_data = validated_data.pop('videos', [])
        
        # Create project
        project = Project.objects.create(
            created_by=self.context['request'].user,
            **validated_data
        )
        
        # Create team members
        for member_data in team_members_data:
            TeamMember.objects.create(project=project, **member_data)
            
        # Create images
        for image_data in images_data:
            ProjectImage.objects.create(project=project, **image_data)
            
        # Create videos
        for video_data in videos_data:
            ProjectVideo.objects.create(project=project, **video_data)
        
        return project


class ProjectUpdateSerializer(serializers.ModelSerializer):
    """Serializer for updating projects"""
    
    team_members = TeamMemberSerializer(many=True, required=False)
    images = ProjectImageSerializer(many=True, required=False)
    videos = ProjectVideoSerializer(many=True, required=False)
    
    class Meta:
        model = Project
        fields = [
            'title', 'description', 'abstract', 'category', 'student_batch', 'github_url', 
            'demo_url', 'project_report', 'team_members', 'images', 'videos'
        ]
    
    def update(self, instance, validated_data):
        team_members_data = validated_data.pop('team_members', None)
        images_data = validated_data.pop('images', None)
        videos_data = validated_data.pop('videos', None)
        
        # Update project fields
        for attr, value in validated_data.items():
            setattr(instance, attr, value)
        instance.save()
        
        # Update team members if provided
        if team_members_data is not None:
            # Remove existing team members
            instance.team_members.all().delete()
            
            # Create new team members
            for member_data in team_members_data:
                TeamMember.objects.create(project=instance, **member_data)
        
        # Update images if provided
        if images_data is not None:
            # Remove existing images
            instance.images.all().delete()
            
            # Create new images
            for image_data in images_data:
                ProjectImage.objects.create(project=instance, **image_data)
                
        # Update videos if provided  
        if videos_data is not None:
            # Remove existing videos
            instance.videos.all().delete()
            
            # Create new videos
            for video_data in videos_data:
                ProjectVideo.objects.create(project=instance, **video_data)
        
        return instance


class ProjectListSerializer(serializers.ModelSerializer):
    """Optimized project serializer for lists - minimal data for fast loading"""
    
    created_by_name = serializers.SerializerMethodField()
    team_count = serializers.SerializerMethodField()
    thumbnail_image = serializers.SerializerMethodField()
    technologies = serializers.SerializerMethodField()
    status = serializers.SerializerMethodField()
    
    class Meta:
        model = Project
        fields = [
            'id', 'title', 'description', 'category', 'student_batch',
            'github_url', 'demo_url', 'thumbnail_image', 'is_featured',
            'created_by_name', 'team_count', 'technologies', 'status', 'created_at'
        ]
    
    def get_created_by_name(self, obj):
        """Get creator's full name or username"""
        if obj.created_by:
            full_name = f"{obj.created_by.first_name} {obj.created_by.last_name}".strip()
            return full_name if full_name else obj.created_by.username
        return None
    
    def get_team_count(self, obj):
        """Include creator + team members"""
        return obj.team_members.count() + 1
    
    def get_thumbnail_image(self, obj):
        """Get project thumbnail image - prioritize direct project_images field, then gallery"""
        # First priority: Direct project_images field (main cover image)
        if obj.project_images:
            return obj.project_images.url
        
        # Second priority: Featured gallery image
        featured_image = obj.images.filter(is_featured=True).first()
        if featured_image and featured_image.image:
            return featured_image.image.url
            
        # Third priority: First gallery image
        first_image = obj.images.first()
        if first_image and first_image.image:
            return first_image.image.url
            
        return None
    
    def get_technologies(self, obj):
        """Extract technologies from description/abstract (placeholder)"""
        # You can implement actual technology extraction logic here
        # For now, return common tech categories based on project category
        tech_mapping = {
            'web_development': ['React', 'Node.js', 'JavaScript'],
            'mobile_app': ['React Native', 'Flutter', 'Android'],
            'machine_learning': ['Python', 'TensorFlow', 'scikit-learn'],
            'iot': ['Arduino', 'Raspberry Pi', 'Sensors'],
            'data_science': ['Python', 'Pandas', 'NumPy'],
            'ai': ['Python', 'TensorFlow', 'PyTorch'],
        }
        return tech_mapping.get(obj.category, [obj.category.replace('_', ' ').title()])
    
    def get_status(self, obj):
        """Determine project status (placeholder logic)"""
        # You can implement actual status logic here
        return 'completed'  # Default status
