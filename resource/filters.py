import django_filters
from .models import Resource

class ResourceFilter(django_filters.FilterSet):
    resource_type = django_filters.ChoiceFilter(
        choices=Resource.RESOURCE_TYPE_CHOICES
    )
    uploaded_after = django_filters.DateFilter(
        field_name='uploaded_at',
        lookup_expr='gte'
    )
    uploaded_before = django_filters.DateFilter(
        field_name='uploaded_at',
        lookup_expr='lte'
    )
    min_size = django_filters.NumberFilter(
        field_name='size',
        lookup_expr='gte'
    )
    max_size = django_filters.NumberFilter(
        field_name='size',
        lookup_expr='lte'
    )

    class Meta:
        model = Resource
        fields = {
            'title': ['icontains'],
            'description': ['icontains'],
            'uploaded_by': ['exact'],
            'is_public': ['exact'],
        }