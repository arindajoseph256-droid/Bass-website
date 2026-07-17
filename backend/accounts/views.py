from rest_framework import status, generics
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import OutstandingToken, BlacklistedToken
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.utils.encoding import force_str, force_bytes
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.contrib.auth.tokens import default_token_generator
from django.conf import settings

from .serializers import (
    UserRegistrationSerializer,
    UserSerializer,
    UserMinimalSerializer,
    UserPublicSerializer,
    PasswordChangeSerializer,
    PasswordResetSerializer,
    PasswordResetConfirmSerializer,
    LoginSerializer,
)

User = get_user_model()


class RegisterView(generics.CreateAPIView):
    """Register a new user."""

    queryset = User.objects.all()
    serializer_class = UserRegistrationSerializer
    permission_classes = [AllowAny]

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            "success": True,
            "message": "Registration successful.",
            "user": UserSerializer(user).data,
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
        }, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """Authenticate user and return tokens."""

    permission_classes = [AllowAny]
    serializer_class = LoginSerializer

    def post(self, request):
        serializer = LoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data["email"]
        password = serializer.validated_data["password"]
        remember_me = serializer.validated_data.get("remember_me", False)
        
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            return Response({
                "success": False,
                "message": "Invalid email or password.",
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not user.check_password(password):
            return Response({
                "success": False,
                "message": "Invalid email or password.",
            }, status=status.HTTP_401_UNAUTHORIZED)
        
        if not user.is_active:
            return Response({
                "success": False,
                "message": "Account is disabled.",
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Update last activity
        user.update_last_activity()
        user.last_login_ip = self.get_client_ip(request)
        user.save(update_fields=["last_activity", "last_login_ip"])
        
        # Generate tokens
        refresh = RefreshToken.for_user(user)
        
        # Set token expiry based on remember_me
        if remember_me:
            refresh.set_exp(lifetime=timezone.timedelta(days=30))
        
        return Response({
            "success": True,
            "message": "Login successful.",
            "user": UserSerializer(user).data,
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
        })

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0]
        return request.META.get("REMOTE_ADDR")


class LogoutView(APIView):
    """Logout user and blacklist tokens."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if refresh_token:
                token = RefreshToken(refresh_token)
                token.blacklist()
            return Response({
                "success": True,
                "message": "Logout successful.",
            })
        except Exception:
            return Response({
                "success": False,
                "message": "Invalid token.",
            }, status=status.HTTP_400_BAD_REQUEST)


class RefreshTokenView(APIView):
    """Refresh access token."""

    permission_classes = [AllowAny]

    def post(self, request):
        try:
            refresh_token = request.data.get("refresh")
            if not refresh_token:
                return Response({
                    "success": False,
                    "message": "Refresh token is required.",
                }, status=status.HTTP_400_BAD_REQUEST)
            
            refresh = RefreshToken(refresh_token)
            
            return Response({
                "success": True,
                "tokens": {
                    "refresh": str(refresh),
                    "access": str(refresh.access_token),
                },
            })
        except Exception:
            return Response({
                "success": False,
                "message": "Invalid or expired refresh token.",
            }, status=status.HTTP_401_UNAUTHORIZED)


class UserProfileView(generics.RetrieveUpdateAPIView):
    """Get or update current user profile."""

    serializer_class = UserSerializer
    permission_classes = [IsAuthenticated]

    def get_object(self):
        return self.request.user

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "success": True,
            "user": serializer.data,
        })

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()
        serializer = self.get_serializer(instance, data=request.data, partial=partial)
        serializer.is_valid(raise_exception=True)
        serializer.save()
        
        return Response({
            "success": True,
            "message": "Profile updated successfully.",
            "user": serializer.data,
        })


class UserPublicProfileView(generics.RetrieveAPIView):
    """Get public profile of any user."""

    queryset = User.objects.filter(is_active=True, is_public=True)
    serializer_class = UserPublicSerializer
    permission_classes = [AllowAny]
    lookup_field = "id"
    lookup_url_kwarg = "user_id"


class ChangePasswordView(APIView):
    """Change user password."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        serializer = PasswordChangeSerializer(data=request.data, context={"request": request})
        serializer.is_valid(raise_exception=True)
        
        user = request.user
        user.set_password(serializer.validated_data["new_password"])
        user.save()
        
        # Blacklist all existing tokens
        OutstandingToken.objects.filter(user=user).delete()
        
        # Generate new tokens
        refresh = RefreshToken.for_user(user)
        
        return Response({
            "success": True,
            "message": "Password changed successfully.",
            "tokens": {
                "refresh": str(refresh),
                "access": str(refresh.access_token),
            },
        })


class PasswordResetRequestView(APIView):
    """Request password reset email."""

    permission_classes = [AllowAny]
    serializer_class = PasswordResetSerializer

    def post(self, request):
        serializer = PasswordResetSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        email = serializer.validated_data["email"]
        user = User.objects.get(email=email)
        
        # Generate reset token
        token = default_token_generator.make_token(user)
        uid = urlsafe_base64_encode(force_bytes(user.pk))
        
        # In production, send email here
        reset_url = f"{settings.FRONTEND_URL}/reset-password/{uid}/{token}/"
        
        return Response({
            "success": True,
            "message": "Password reset email sent.",
            # Include URL for development only
            "reset_url": reset_url if settings.DEBUG else None,
        })


class PasswordResetConfirmView(APIView):
    """Confirm password reset with token."""

    permission_classes = [AllowAny]

    def post(self, request, uidb64, token):
        serializer = PasswordResetConfirmSerializer(
            data=request.data,
            context={"uidb64": uidb64, "token": token}
        )
        serializer.is_valid(raise_exception=True)
        
        user = serializer.validated_data["user"]
        user.set_password(serializer.validated_data["new_password"])
        user.password_reset_token = ""
        user.save()
        
        return Response({
            "success": True,
            "message": "Password reset successful.",
        })


class DeactivateAccountView(APIView):
    """Deactivate user account."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user
        user.is_active = False
        user.save(update_fields=["is_active"])
        
        # Blacklist all tokens
        OutstandingToken.objects.filter(user=user).delete()
        
        return Response({
            "success": True,
            "message": "Account deactivated successfully.",
        })


class DeleteAccountView(APIView):
    """Permanently delete user account."""

    permission_classes = [IsAuthenticated]

    def delete(self, request):
        user = request.user
        
        # Soft delete or hard delete based on requirements
        # For GDPR compliance, typically soft delete with scheduled hard delete
        user.is_active = False
        user.email = f"deleted_{user.id}@deleted.com"
        user.username = f"deleted_{user.id}"
        user.save()
        
        return Response({
            "success": True,
            "message": "Account deleted successfully.",
        })


class UserListView(generics.ListAPIView):
    """List users (admin only)."""

    queryset = User.objects.filter(is_active=True)
    serializer_class = UserMinimalSerializer
    permission_classes = [IsAuthenticated]
    filterset_fields = ["role", "is_verified"]
    search_fields = ["email", "first_name", "last_name", "username"]
