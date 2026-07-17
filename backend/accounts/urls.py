from django.urls import path
from .views import (
    RegisterView,
    LoginView,
    LogoutView,
    RefreshTokenView,
    UserProfileView,
    UserPublicProfileView,
    ChangePasswordView,
    PasswordResetRequestView,
    PasswordResetConfirmView,
    DeactivateAccountView,
    DeleteAccountView,
    UserListView,
)

urlpatterns = [
    # Authentication
    path("register/", RegisterView.as_view(), name="register"),
    path("login/", LoginView.as_view(), name="login"),
    path("logout/", LogoutView.as_view(), name="logout"),
    path("token/refresh/", RefreshTokenView.as_view(), name="token_refresh"),
    
    # Profile
    path("profile/", UserProfileView.as_view(), name="profile"),
    path("profile/<int:user_id>/", UserPublicProfileView.as_view(), name="public_profile"),
    
    # Password
    path("password/change/", ChangePasswordView.as_view(), name="password_change"),
    path("password/reset/", PasswordResetRequestView.as_view(), name="password_reset"),
    path("password/reset/<uidb64>/<token>/", PasswordResetConfirmView.as_view(), name="password_reset_confirm"),
    
    # Account Management
    path("deactivate/", DeactivateAccountView.as_view(), name="deactivate"),
    path("delete/", DeleteAccountView.as_view(), name="delete"),
    
    # Admin
    path("users/", UserListView.as_view(), name="user_list"),
]
