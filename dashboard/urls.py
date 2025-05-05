from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import StudyGroupViewSet, StudySessionViewSet, ResourceViewSet, UserActivityViewSet

router = DefaultRouter()
router.register(r'groups', StudyGroupViewSet)
router.register(r'sessions', StudySessionViewSet)
router.register(r'resources', ResourceViewSet)
router.register(r'activities', UserActivityViewSet)

urlpatterns = [
    path('a/', include(router.urls)),
]
