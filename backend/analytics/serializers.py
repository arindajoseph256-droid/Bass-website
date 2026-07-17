from rest_framework import serializers
from .models import DailyStats, CourseAnalytics, UserActivity


class DailyStatsSerializer(serializers.ModelSerializer):
    class Meta:
        model = DailyStats
        fields = "__all__"


class CourseAnalyticsSerializer(serializers.ModelSerializer):
    course_title = serializers.CharField(source="course.title", read_only=True)

    class Meta:
        model = CourseAnalytics
        fields = [
            "id", "course", "course_title", "views", "unique_views",
            "enrollments", "completions", "average_progress",
            "average_rating", "completion_rate",
        ]


class UserActivitySerializer(serializers.ModelSerializer):
    user_email = serializers.CharField(source="user.email", read_only=True)

    class Meta:
        model = UserActivity
        fields = ["id", "user", "user_email", "activity_type", "resource_type", "created_at"]
