from rest_framework import serializers
from accounts.models import User, UserSession


class UserSessionSerializer(serializers.ModelSerializer):
    class Meta:
        model = UserSession
        fields = ["id", "ip_address", "created_at", "expires_at", "is_active"]
