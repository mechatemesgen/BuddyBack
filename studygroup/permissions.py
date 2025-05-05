from rest_framework import permissions

class IsGroupMemberOrPublic(permissions.BasePermission):
    """
    Object-level permission to only allow members to view private groups
    or anyone to view public groups.
    """
    def has_object_permission(self, request, view, obj):
        if obj.privacy == 'PUBLIC':
            return True
        
        if request.method in permissions.SAFE_METHODS:
            return obj.members.filter(id=request.user.id).exists()
        
        return obj.creator == request.user or obj.memberships.filter(
            user=request.user, 
            role__in=['ADMIN', 'MODERATOR']
        ).exists()