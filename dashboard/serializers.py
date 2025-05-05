from rest_framework import serializers
from .models import StudyGroup, StudySession, Resource, UserActivity


class StudyGroupSerializer(serializers.ModelSerializer):
    class Meta:
        model = StudyGroup
        fields = ['id', 'name', 'subject', 'description', 'created_at', 'members']
        read_only_fields = ['members']


class StudySessionSerializer(serializers.ModelSerializer):
    group_name = serializers.CharField(source='group.name', read_only=True)

    class Meta:
        model = StudySession
        fields = ['id', 'title', 'group', 'group_name', 'start_time', 'end_time', 'attendees']
        read_only_fields = ['attendees']

    def create(self, validated_data):
        session = StudySession.objects.create(**validated_data)
        session.attendees.add(self.context['request'].user)
        return session


class ResourceSerializer(serializers.ModelSerializer):
    class Meta:
        model = Resource
        fields = ['id', 'title', 'file', 'file_type', 'size', 'uploaded_by', 'uploaded_at', 'groups']
        read_only_fields = ['uploaded_by', 'uploaded_at']


class UserActivitySerializer(serializers.ModelSerializer):
    class Meta:
        model = UserActivity
        fields = ['id', 'user', 'study_hours', 'sessions_attended', 'groups_joined', 'resources_shared', 'last_updated']
        read_only_fields = ['user', 'last_updated']
