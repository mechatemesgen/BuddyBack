from django.urls import path
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
    TokenRefreshView,
    TokenVerifyView
)
from .views import (
    RegisterView,
    LoginUserView,
    UserProfileView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    LogoutView,
    LogoutAllView,
    UserSettingsView
)

urlpatterns = [
    path('register/', RegisterView.as_view(), name='register'),
    path('login/', LoginUserView.as_view(), name='login'),

    path('profile/', UserProfileView.as_view(), name='user-profile'),
    path('profile/<int:user_id>/', UserProfileView.as_view(), name='user-profile-admin'),

    path('password-reset/', PasswordResetRequestView.as_view(), name='password-reset-request'),
    path('password-reset/confirm/', PasswordResetConfirmView.as_view(), name='password-reset-confirm'),

    path('logout/', LogoutView.as_view(), name='logout'),
    path('logout/all/', LogoutAllView.as_view(), name='logout-all'),

    path('settings/', UserSettingsView.as_view(), name='user-settings'),

    path('token/', TokenObtainPairView.as_view(), name='token_obtain_pair'),        
    path('token/refresh/', TokenRefreshView.as_view(), name='token_refresh'),       
    path('token/verify/', TokenVerifyView.as_view(), name='token_verify'),         
]
