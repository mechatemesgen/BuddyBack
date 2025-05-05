from rest_framework import generics, permissions, filters, status
from django_filters.rest_framework import DjangoFilterBackend
from rest_framework.response import Response
from django.shortcuts import get_object_or_404
from rest_framework.exceptions import PermissionDenied

from .models import StudyGroup, Subject, GroupChat
from .serializers import (
    StudyGroupSerializer,
    StudyGroupCreateSerializer,
    SubjectSerializer,
    GroupChatSerializer,
)
from .filters import StudyGroupFilter
from .permissions import IsGroupMemberOrPublic


class GroupChatDetailAPI(generics.RetrieveAPIView):
    """
    GET /groups/<group_id>/chats/<pk>/
    Retrieve a specific chat message in a study group.
    """
    serializer_class = GroupChatSerializer
    permission_classes = [permissions.IsAuthenticated]

    def get_object(self):
        group_id = self.kwargs['group_id']
        chat_id = self.kwargs['pk']
        
        # Verify group exists and user is a member
        group = get_object_or_404(StudyGroup, id=group_id)
        if not group.members.filter(id=self.request.user.id).exists():
            raise PermissionDenied("You are not a member of this group")
        
        chat = get_object_or_404(GroupChat, id=chat_id, group_id=group_id)
        return chat


class GroupChatListCreateAPI(generics.ListCreateAPIView):
    """
    GET /groups/<group_id>/chats/
    List all chats for a study group.

    POST /groups/<group_id>/chats/
    Create a new chat in the study group.
    """
    serializer_class = GroupChatSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.OrderingFilter]
    ordering_fields = ['timestamp']
    ordering = ['-timestamp']

    def get_queryset(self):
        group_id = self.kwargs['group_id']
        group = get_object_or_404(StudyGroup, id=group_id)
        
        # Verify user is a member of the group
        if not group.members.filter(id=self.request.user.id).exists():
            return GroupChat.objects.none()
        
        return GroupChat.objects.filter(group_id=group_id)

    def perform_create(self, serializer):
        group_id = self.kwargs['group_id']
        group = get_object_or_404(StudyGroup, id=group_id)
        
        # Verify user is a member of the group
        if not group.members.filter(id=self.request.user.id).exists():
            raise PermissionDenied("You are not a member of this group")
        
        serializer.save(user=self.request.user, group=group)


class SubjectListAPI(generics.ListAPIView):
    """
    GET /subjects/
    List all available subjects.
    """
    queryset = Subject.objects.all()
    serializer_class = SubjectSerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None
    filter_backends = [filters.SearchFilter]
    search_fields = ['name', 'code']


class StudyGroupListCreateAPI(generics.ListCreateAPIView):
    """
    GET /groups/
    List study groups with search, filtering, and ordering.

    POST /groups/
    Create a new study group. Authenticated users only.
    """
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend, filters.SearchFilter, filters.OrderingFilter]
    filterset_class = StudyGroupFilter
    search_fields = ['name', 'description', 'subject__name']
    ordering_fields = ['name', 'created_at', 'updated_at', 'member_count']
    ordering = ['-created_at']

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return StudyGroupCreateSerializer
        return StudyGroupSerializer

    def get_queryset(self):
        queryset = StudyGroup.objects.annotate_member_count()
        
        if self.request.user.is_authenticated:
            if self.request.query_params.get('my_groups'):
                return queryset.filter(members=self.request.user)
            return queryset.filter(
                models.Q(privacy='PUBLIC') | 
                models.Q(members=self.request.user)
            ).distinct()
        
        # For anonymous users, only show public groups
        return queryset.filter(privacy='PUBLIC')

    def perform_create(self, serializer):
        serializer.save(creator=self.request.user)


class StudyGroupDetailAPI(generics.RetrieveUpdateDestroyAPIView):
    """
    GET /groups/<id>/
    Retrieve a specific study group.

    PUT /groups/<id>/ or PATCH
    Update a study group (only allowed by owner or permitted users).

    DELETE /groups/<id>/
    Delete a study group.
    """
    queryset = StudyGroup.objects.annotate_member_count()
    serializer_class = StudyGroupSerializer
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsGroupMemberOrPublic]

    def perform_update(self, serializer):
        # Only allow creator or admins to update
        if (self.request.user != serializer.instance.creator and 
            not serializer.instance.memberships.filter(
                user=self.request.user, 
                role__in=['ADMIN', 'MODERATOR']
            ).exists()):
            raise PermissionDenied("Only group creator or admins can update this group")
        serializer.save()


class MyStudyGroupsAPI(generics.ListAPIView):
    """
    GET /groups/my/
    List study groups that the current user is a member of.
    """
    serializer_class = StudyGroupSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [filters.SearchFilter, filters.OrderingFilter]
    search_fields = ['name', 'description', 'subject__name']
    ordering_fields = ['name', 'created_at', 'updated_at']
    ordering = ['-created_at']

    def get_queryset(self):
        return StudyGroup.objects.filter(
            members=self.request.user
        ).annotate_member_count()
