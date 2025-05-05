from rest_framework import serializers
from .models import Resource, ResourceCategory
from users.serializers import UserProfileSerializer
from studygroup.serializers import StudyGroupSerializer
from studygroup.models import StudyGroup


class ResourceCategorySerializer(serializers.ModelSerializer):
    """
    Serializer for ResourceCategory model
    """
    class Meta:
        model = ResourceCategory
        fields = ['id', 'name', 'slug', 'description', 'icon']
        read_only_fields = ['slug']


class ResourceSerializer(serializers.ModelSerializer):
    """
    Detailed serializer for Resource listing with nested relationships
    """
    uploaded_by = UserProfileSerializer(read_only=True)
    groups = StudyGroupSerializer(many=True, read_only=True)
    categories = ResourceCategorySerializer(many=True, read_only=True)
    
    # Computed fields
    file_url = serializers.SerializerMethodField()
    file_extension = serializers.SerializerMethodField()
    formatted_size = serializers.SerializerMethodField()
    is_owner = serializers.SerializerMethodField()

    class Meta:
        model = Resource
        fields = [
            'id', 'title', 'description', 'file', 'file_url',
            'file_extension', 'resource_type', 'formatted_size',
            'uploaded_by', 'groups', 'categories', 'uploaded_at',
            'updated_at', 'download_count', 'is_public', 'is_owner'
        ]
        read_only_fields = [
            'file_url', 'file_extension', 'formatted_size',
            'uploaded_by', 'uploaded_at', 'updated_at', 'download_count'
        ]

    def get_file_url(self, obj):
        """Generate absolute URL for the resource file"""
        request = self.context.get('request')
        return request.build_absolute_uri(obj.file.url) if obj.file and request else None

    def get_file_extension(self, obj):
        """Get uppercase file extension"""
        return obj.file_extension

    def get_formatted_size(self, obj):
        """Return human-readable file size"""
        return obj.formatted_size

    def get_is_owner(self, obj):
        """Check if current user is the resource owner"""
        request = self.context.get('request')
        return request and request.user.is_authenticated and obj.uploaded_by == request.user


class ResourceCreateSerializer(serializers.ModelSerializer):
    
    """
    Serializer for Resource creation with file upload
    """
    groups = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=StudyGroup.objects.all(),
        required=False,
        help_text="List of group IDs this resource belongs to"
    )
    categories = serializers.PrimaryKeyRelatedField(
        many=True,
        queryset=ResourceCategory.objects.all(),
        required=False,
        help_text="List of category IDs for this resource"
    )
    file = serializers.FileField(
        required=True,
        help_text="The file to upload",
        error_messages={
            'required': 'Please select a file to upload'
        }
    )

    class Meta:
        model = Resource
        fields = [
            'title', 'description', 'file', 'resource_type',
            'groups', 'categories', 'is_public'
        ]
        extra_kwargs = {
            'resource_type': {
                'choices': Resource.RESOURCE_TYPE_CHOICES,
                'error_messages': {
                    'invalid_choice': f"Invalid resource type. Valid choices are: {[choice[0] for choice in Resource.RESOURCE_TYPE_CHOICES]}"
                },
                'help_text': f"Resource type: {[choice[0] for choice in Resource.RESOURCE_TYPE_CHOICES]}"
            }
        }

    def validate(self, data):
        """Validate group membership and auto-detect resource type"""
        request = self.context.get('request')
        
        # Validate group membership
        if 'groups' in data:
            for group in data['groups']:
                if not group.members.filter(id=request.user.id).exists():
                    raise serializers.ValidationError(
                        {"groups": f"You are not a member of group: {group.name}"}
                    )

        if 'file' in data:
            if not data.get('resource_type'):
                extension = data['file'].name.split('.')[-1].lower()
                for resource_type, extensions in Resource.FILE_EXTENSIONS.items():
                    if extension in extensions:
                        data['resource_type'] = resource_type
                        break
                else:
                    data['resource_type'] = 'OTHER'
            
            if data.get('resource_type') in Resource.FILE_EXTENSIONS:
                extension = data['file'].name.split('.')[-1].lower()
                if extension not in Resource.FILE_EXTENSIONS[data['resource_type']]:
                    raise serializers.ValidationError(
                        {"file": f"File extension doesn't match resource type {data['resource_type']}"}
                    )

        return data

    def create(self, validated_data):
        """Create resource with groups and categories"""
        groups = validated_data.pop('groups', [])
        categories = validated_data.pop('categories', [])
        validated_data['uploaded_by'] = self.context['request'].user

        resource = super().create(validated_data)
        resource.groups.set(groups)
        resource.categories.set(categories)
        return resource


class ResourceUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer for updating Resource metadata (excluding file)
    """
    class Meta:
        model = Resource
        fields = ['title', 'description', 'resource_type', 'is_public']
        extra_kwargs = {
            'resource_type': {
                'choices': Resource.RESOURCE_TYPE_CHOICES,
                'error_messages': {
                    'invalid_choice': f"Invalid resource type. Valid choices are: {[choice[0] for choice in Resource.RESOURCE_TYPE_CHOICES]}"
                },
                'help_text': f"Resource type: {[choice[0] for choice in Resource.RESOURCE_TYPE_CHOICES]}"
            }
        }