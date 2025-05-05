from django.urls import path
from .views import (
    ResourceCategoryListAPI,
    ResourceListCreateAPI,
    ResourceDetailAPI,
    ResourceDownloadAPI,
    MyResourcesAPI
)

urlpatterns = [
    path('categories/', ResourceCategoryListAPI.as_view(), name='resource-category-list'),
    path('resources/', ResourceListCreateAPI.as_view(), name='resource-list-create'),
    path('resources/<int:pk>/', ResourceDetailAPI.as_view(), name='resource-detail'),
    path('resources/<int:pk>/download/', ResourceDownloadAPI.as_view(), name='resource-download'),
    path('resources/my/', MyResourcesAPI.as_view(), name='my-resources'),
]