from django.shortcuts import get_object_or_404
from django.http import FileResponse
from django.db.models import Q

from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.parsers import MultiPartParser, FormParser,JSONParser

from django_filters.rest_framework import DjangoFilterBackend

from .models import Resource, ResourceCategory
from .serializers import (
    ResourceSerializer,
    ResourceCreateSerializer,
    ResourceUpdateSerializer,
    ResourceCategorySerializer
)
from .filters import ResourceFilter
from .permissions import IsResourceOwnerOrReadOnly


class ResourceCategoryListAPI(generics.ListAPIView):
    queryset = ResourceCategory.objects.all()
    serializer_class = ResourceCategorySerializer
    permission_classes = [permissions.AllowAny]
    pagination_class = None  




class ResourceListCreateAPI(generics.ListCreateAPIView):
    parser_classes = [MultiPartParser, FormParser, JSONParser]
    queryset = Resource.objects.select_related('uploaded_by')\
                               .prefetch_related('groups', 'categories')
    permission_classes = [permissions.IsAuthenticatedOrReadOnly]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ResourceFilter

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return ResourceCreateSerializer
        return ResourceSerializer

    def get_queryset(self):
        queryset = super().get_queryset()
        
class ResourceDetailAPI(generics.RetrieveUpdateDestroyAPIView):
    queryset = Resource.objects.select_related('uploaded_by')\
                               .prefetch_related('groups', 'categories')
    permission_classes = [permissions.IsAuthenticatedOrReadOnly, IsResourceOwnerOrReadOnly]

    def get_serializer_class(self):
        if self.request.method in ['PUT', 'PATCH']:
            return ResourceUpdateSerializer
        return ResourceSerializer



class ResourceDownloadAPI(generics.RetrieveAPIView):
    queryset = Resource.objects.all()
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = ResourceSerializer

    def get(self, request, *args, **kwargs):
        resource = self.get_object()

        if not (resource.is_public or 
                resource.uploaded_by == request.user or
                resource.groups.filter(members=request.user).exists()):
            return Response(
                {"detail": "You don't have permission to download this resource."},
                status=status.HTTP_403_FORBIDDEN
            )

        resource.increment_download_count()

        response = FileResponse(resource.file.open('rb'))
        response['Content-Disposition'] = f'attachment; filename="{resource.file.name}"'
        return response



class MyResourcesAPI(generics.ListAPIView):
    serializer_class = ResourceSerializer
    permission_classes = [permissions.IsAuthenticated]
    filter_backends = [DjangoFilterBackend]
    filterset_class = ResourceFilter

    def get_queryset(self):
        return Resource.objects.filter(
            uploaded_by=self.request.user
        ).select_related('uploaded_by')\
         .prefetch_related('groups', 'categories')
