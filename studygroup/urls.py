from django.urls import path

from . import views

urlpatterns = [
    path('groups/<int:group_id>/chats/<int:pk>/', views.GroupChatDetailAPI.as_view(), name='group-chat-detail'),

    path('groups/<int:group_id>/chats/', views.GroupChatListCreateAPI.as_view(), name='group-chat-list-create'),

    path('subjects/', views.SubjectListAPI.as_view(), name='subject-list'),

    path('groups/', views.StudyGroupListCreateAPI.as_view(), name='study-group-list-create'),

    path('groups/<int:pk>/', views.StudyGroupDetailAPI.as_view(), name='study-group-detail'),

    path('groups/my/', views.MyStudyGroupsAPI.as_view(), name='my-study-groups'),
]
