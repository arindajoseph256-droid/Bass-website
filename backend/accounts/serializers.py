from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.contrib.auth.password_validation import validate_password
from django.core.exceptions import ValidationError
from django.contrib.auth.tokens import default_token_generator
from django.utils.http import urlsafe_base64_encode, urlsafe_base64_decode
from django.utils.encoding import force_bytes, force_str

User = get_user_model()


class UserRegistrationSerializer(serializers.ModelSerializer):
    """Serializer for user registration."""

    password = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
    )
    password_confirm = serializers.CharField(
        write_only=True,
        required=True,
        style={"input_type": "password"},
    )

    class Meta:
        model = User
        fields = [
            "id", "email", "username", "first_name", "last_name",
            "password", "password_confirm", "role", "phone", "gender",
        ]
        extra_kwargs = {
            "first_name": {"required": True},
            "last_name": {"required": True},
        }

    def validate(self, attrs):
        if attrs["password"] != attrs["password_confirm"]:
            raise serializers.ValidationError(
                {"password_confirm": "Passwords do not match."}
            )
        try:
            validate_password(attrs["password"])
        except ValidationError as e:
            raise serializers.ValidationError({"password": list(e.messages)})
        return attrs

    def create(self, validated_data):
        validated_data.pop("password_confirm")
        user = User.objects.create_user(**validated_data)
        return user


class UserSerializer(serializers.ModelSerializer):
    """Serializer for user profile."""

    class Meta:
        model = User
        fields = [
            "id", "email", "username", "first_name", "last_name",
            "role", "gender", "phone", "bio", "date_of_birth",
            "profile_image", "cover_image", "address", "city",
            "country", "postal_code", "website", "linkedin",
            "twitter", "github", "email_notifications", "push_notifications",
            "language", "timezone", "dark_mode", "badges", "points",
            "is_public", "show_email", "show_profile", "is_verified",
            "date_joined", "last_login", "last_activity",
        ]
        read_only_fields = [
            "id", "email", "role", "badges", "points",
            "is_verified", "date_joined", "last_login", "last_activity",
        ]


class UserMinimalSerializer(serializers.ModelSerializer):
    """Minimal user serializer for embedding."""

    class Meta:
        model = User
        fields = [
            "id", "username", "first_name", "last_name",
            "profile_image", "role", "is_verified",
        ]
        read_only_fields = fields


class UserPublicSerializer(serializers.ModelSerializer):
    """Public user serializer."""

    class Meta:
        model = User
        fields = [
            "id", "username", "first_name", "last_name",
            "profile_image", "bio", "role", "city", "country",
            "website", "linkedin", "twitter", "github",
            "badges", "points", "is_verified",
        ]
        read_only_fields = fields


class PasswordChangeSerializer(serializers.Serializer):
    """Serializer for password change."""

    old_password = serializers.CharField(required=True, style={"input_type": "password"})
    new_password = serializers.CharField(required=True, style={"input_type": "password"})
    new_password_confirm = serializers.CharField(required=True, style={"input_type": "password"})

    def validate_old_password(self, value):
        user = self.context["request"].user
        if not user.check_password(value):
            raise serializers.ValidationError("Old password is incorrect.")
        return value

    def validate(self, attrs):
        if attrs["new_password"] != attrs["new_password_confirm"]:
            raise serializers.ValidationError(
                {"new_password_confirm": "New passwords do not match."}
            )
        try:
            validate_password(attrs["new_password"], self.context["request"].user)
        except ValidationError as e:
            raise serializers.ValidationError({"new_password": list(e.messages)})
        return attrs


class PasswordResetSerializer(serializers.Serializer):
    """Serializer for password reset request."""

    email = serializers.EmailField(required=True)

    def validate_email(self, value):
        user = self.get_user(value)
        if not user:
            raise serializers.ValidationError("User with this email does not exist.")
        if not user.is_active:
            raise serializers.ValidationError("User account is disabled.")
        return value

    def get_user(self, email):
        try:
            return User.objects.get(email=email)
        except User.DoesNotExist:
            return None


class PasswordResetConfirmSerializer(serializers.Serializer):
    """Serializer for password reset confirmation."""

    token = serializers.CharField(required=True)
    uidb64 = serializers.CharField(required=True)
    new_password = serializers.CharField(required=True, style={"input_type": "password"})

    def validate(self, attrs):
        try:
            uid = force_str(urlsafe_base64_decode(attrs["uidb64"]))
            user = User.objects.get(pk=uid)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError({"token": "Invalid token."})

        if not default_token_generator.check_token(user, attrs["token"]):
            raise serializers.ValidationError({"token": "Invalid or expired token."})

        attrs["user"] = user
        try:
            validate_password(attrs["new_password"], user)
        except ValidationError as e:
            raise serializers.ValidationError({"new_password": list(e.messages)})
        return attrs


class EmailVerificationSerializer(serializers.Serializer):
    """Serializer for email verification."""

    token = serializers.CharField(required=True)

    def validate_token(self, value):
        try:
            uidb64 = self.context.get("uidb64")
            uid = force_str(urlsafe_base64_decode(uidb64))
            user = User.objects.get(pk=uid, verification_token=value)
        except (TypeError, ValueError, OverflowError, User.DoesNotExist):
            raise serializers.ValidationError("Invalid verification token.")
        self.context["user"] = user
        return value


class LoginSerializer(serializers.Serializer):
    """Serializer for user login."""

    email = serializers.EmailField(required=True)
    password = serializers.CharField(
        required=True,
        write_only=True,
        style={"input_type": "password"},
    )
    remember_me = serializers.BooleanField(default=False)


class SocialLoginSerializer(serializers.Serializer):
    """Serializer for social login."""

    provider = serializers.ChoiceField(choices=["google", "facebook", "github"])
    access_token = serializers.CharField(required=True)
