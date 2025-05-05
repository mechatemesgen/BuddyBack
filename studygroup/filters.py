import django_filters
from .models import StudyGroup

class StudyGroupFilter(django_filters.FilterSet):
    subject = django_filters.CharFilter(field_name='subject__name', lookup_expr='iexact')
    privacy = django_filters.ChoiceFilter(choices=StudyGroup.PRIVACY_CHOICES)
    created_after = django_filters.DateFilter(field_name='created_at', lookup_expr='gte')
    created_before = django_filters.DateFilter(field_name='created_at', lookup_expr='lte')

    class Meta:
        model = StudyGroup
        fields = {
            'name': ['icontains'],
            'description': ['icontains'],
        }