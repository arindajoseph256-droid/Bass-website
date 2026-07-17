from rest_framework import serializers
from .models import School, SchoolMembership


class SchoolSerializer(serializers.ModelSerializer):
    class Meta:
        model = School
        fields = "__all__"


class SchoolMembershipSerializer(serializers.ModelSerializer):
    school_name = serializers.CharField(source="school.name", read_only=True)
    user_name = serializers.SerializerMethodField()

    class Meta:
        model = SchoolMembership
        fields = ["id", "school", "school_name", "role", "is_active", "joined_at"]

    def get_user_name(self, obj):
        return obj.user.get_full_name()
