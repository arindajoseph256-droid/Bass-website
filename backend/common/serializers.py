from rest_framework import serializers
from django.contrib.auth import get_user_model

User = get_user_model()


class UserMinimalSerializer(serializers.ModelSerializer):
    """Minimal user serializer for embedding in other serializers."""

    class Meta:
        model = User
        fields = ["id", "username", "email", "first_name", "last_name", "profile_image"]
        read_only_fields = fields


class DynamicFieldsMixin:
    """Mixin to dynamically include/exclude fields based on request context."""

    def __init__(self, *args, **kwargs):
        super().__init__(*args, **kwargs)
        request = self.context.get("request")
        if request:
            fields = request.query_params.get("fields")
            if fields:
                field_names = fields.split(",")
                allowed = set(field_names)
                existing = set(self.fields.keys())
                for field_name in existing - allowed:
                    self.fields.pop(field_name)
