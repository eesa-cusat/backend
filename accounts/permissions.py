from rest_framework.permissions import BasePermission, SAFE_METHODS


class IsOwnerOrReadOnly(BasePermission):
    """
    Custom permission to only allow owners of an object to edit it.
    """
    def has_object_permission(self, request, view, obj):
        # Read permissions are allowed to any authenticated user
        if request.method in SAFE_METHODS:
            return True
        
        # Write permissions are only allowed to the owner of the object
        return obj.created_by == request.user


class IsAdminOrTechnicalHead(BasePermission):
    """
    Custom permission for admin users or technical heads
    """
    def has_permission(self, request, view):
        if not request.user.is_authenticated:
            return False
        
        # Superusers have all permissions
        if request.user.is_superuser:
            return True
        
        # Check if user is in admin or technical head group
        return request.user.groups.filter(name__in=['Admin', 'Technical Head']).exists()


class IsAcademicsTeamOrReadOnly(BasePermission):
    """
    Permission for academics team (schemes, subjects, notes, projects)
    """
    def has_permission(self, request, view):
        # Read permissions are allowed to anyone
        if request.method in SAFE_METHODS:
            return True
        
        # Write permissions require authentication
        if not request.user.is_authenticated:
            return False
        
        # Superusers have all permissions
        if request.user.is_superuser:
            return True
        
        # Check if user is in academics_team group
        return request.user.groups.filter(name='academics_team').exists()


class IsEventsTeamOrReadOnly(BasePermission):
    """
    Permission for events team
    """
    def has_permission(self, request, view):
        # Read permissions are allowed to anyone
        if request.method in SAFE_METHODS:
            return True
        
        # Write permissions require authentication
        if not request.user.is_authenticated:
            return False
        
        # Superusers have all permissions
        if request.user.is_superuser:
            return True
        
        # Check if user is in events_team group
        return request.user.groups.filter(name='events_team').exists()


class IsCareersTeamOrReadOnly(BasePermission):
    """
    Permission for careers team
    """
    def has_permission(self, request, view):
        # Read permissions are allowed to anyone
        if request.method in SAFE_METHODS:
            return True
        
        # Write permissions require authentication
        if not request.user.is_authenticated:
            return False
        
        # Superusers have all permissions
        if request.user.is_superuser:
            return True
        
        # Check if user is in careers_team group
        return request.user.groups.filter(name='careers_team').exists()


class IsPeopleTeamOrReadOnly(BasePermission):
    """
    Permission for people team (alumni + team members)
    """
    def has_permission(self, request, view):
        # Read permissions are allowed to anyone
        if request.method in SAFE_METHODS:
            return True
        
        # Write permissions require authentication
        if not request.user.is_authenticated:
            return False
        
        # Superusers have all permissions
        if request.user.is_superuser:
            return True
        
        # Check if user is in people_team group
        return request.user.groups.filter(name='people_team').exists()


class IsAuthenticatedUserOrReadOnly(BasePermission):
    """
    Permission that allows authenticated users to write, anyone to read
    """
    def has_permission(self, request, view):
        # Read permissions are allowed to anyone
        if request.method in SAFE_METHODS:
            return True
        
        # Write permissions require authentication
        return request.user.is_authenticated


class IsGalleryManager(BasePermission):
    """
    Permission for gallery management
    Allows Admins, Technical Head, and Events Team to manage gallery
    """
    def has_permission(self, request, view):
        # Read permissions are allowed to anyone
        if request.method in SAFE_METHODS:
            return True
        
        # Write permissions require authentication
        if not request.user.is_authenticated:
            return False
        
        # Superusers have all permissions
        if request.user.is_superuser:
            return True
        
        # Check if user is Admin, Technical Head, or Events Team
        return request.user.groups.filter(
            name__in=['Admin', 'Technical Head', 'events_team']
        ).exists()
