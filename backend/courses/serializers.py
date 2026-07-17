from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.db.models import Avg, Count
from .models import (
    Category, Tag, Course, CourseReview,
    Enrollment, Wishlist, Bookmark,
)

User = get_user_model()


class CategorySerializer(serializers.ModelSerializer):
    """Serializer for course categories."""
    
    course_count = serializers.SerializerMethodField()

    class Meta:
        model = Category
        fields = [
            "id", "name", "slug", "description", "icon",
            "image", "parent", "is_active", "order", "course_count",
        ]

    def get_course_count(self, obj):
        return obj.courses.filter(status=Course.Status.PUBLISHED).count()


class TagSerializer(serializers.ModelSerializer):
    """Serializer for course tags."""

    class Meta:
        model = Tag
        fields = ["id", "name", "slug"]


class TeacherSerializer(serializers.Serializer):
    """Minimal teacher serializer."""

    id = serializers.IntegerField()
    first_name = serializers.CharField()
    last_name = serializers.CharField()
    profile_image = serializers.ImageField()
    bio = serializers.CharField()
    total_courses = serializers.IntegerField()
    total_students = serializers.IntegerField()


class CourseListSerializer(serializers.ModelSerializer):
    """Serializer for course list view."""

    teacher = serializers.SerializerMethodField()
    category = CategorySerializer()
    discount_percentage = serializers.IntegerField()
    duration_formatted = serializers.CharField()
    is_enrolled = serializers.SerializerMethodField()
    is_wishlisted = serializers.SerializerMethodField()

    class Meta:
        model = Course
        fields = [
            "id", "title", "slug", "short_description", "thumbnail",
            "level", "language", "price", "discount_price", "is_free",
            "current_price", "discount_percentage", "duration_formatted",
            "total_students", "total_lessons", "total_rating", "total_reviews",
            "teacher", "category", "is_featured", "is_popular",
            "is_enrolled", "is_wishlisted", "published_at",
        ]

    def get_teacher(self, obj):
        return {
            "id": obj.teacher.id,
            "first_name": obj.teacher.first_name,
            "last_name": obj.teacher.last_name,
            "profile_image": obj.teacher.profile_image.url if obj.teacher.profile_image else None,
        }

    def get_is_enrolled(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return Enrollment.objects.filter(
                student=request.user, course=obj
            ).exists()
        return False

    def get_is_wishlisted(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return Wishlist.objects.filter(
                student=request.user, course=obj
            ).exists()
        return False


class CourseDetailSerializer(CourseListSerializer):
    """Serializer for course detail view."""

    tags = TagSerializer(many=True)
    requirements = serializers.ListField(child=serializers.CharField())
    outcomes = serializers.ListField(child=serializers.CharField())

    class Meta(CourseListSerializer.Meta):
        fields = CourseListSerializer.Meta.fields + [
            "description", "preview_video", "requirements", "outcomes",
            "tags", "allow_guest_access", "certificate_available",
            "max_students", "created_at", "updated_at",
        ]

    def to_representation(self, instance):
        data = super().to_representation(instance)
        # Convert newline-separated text to list
        data["requirements"] = instance.requirements.split("\n") if instance.requirements else []
        data["outcomes"] = instance.outcomes.split("\n") if instance.outcomes else []
        return data


class CourseCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating courses."""

    class Meta:
        model = Course
        fields = [
            "title", "short_description", "description", "thumbnail",
            "preview_video", "level", "language", "price", "discount_price",
            "is_free", "category", "tags", "requirements", "outcomes",
            "status", "is_featured", "allow_guest_access", "certificate_available",
            "max_students", "school",
        ]

    def to_internal_value(self, data):
        # Convert lists to newline-separated strings
        if "requirements" in data:
            data = data.copy()
            data["requirements"] = "\n".join(data.get("requirements", []))
        if "outcomes" in data:
            data = data.copy()
            data["outcomes"] = "\n".join(data.get("outcomes", []))
        return super().to_internal_value(data)


class CourseReviewSerializer(serializers.ModelSerializer):
    """Serializer for course reviews."""

    user = serializers.SerializerMethodField()

    class Meta:
        model = CourseReview
        fields = [
            "id", "course", "user", "rating", "title",
            "comment", "is_approved", "created_at",
        ]
        read_only_fields = ["id", "user", "is_approved", "created_at"]

    def get_user(self, obj):
        return {
            "id": obj.user.id,
            "first_name": obj.user.first_name,
            "last_name": obj.user.last_name,
            "profile_image": obj.user.profile_image.url if obj.user.profile_image else None,
        }


class EnrollmentSerializer(serializers.ModelSerializer):
    """Serializer for course enrollments."""

    course = CourseListSerializer(read_only=True)
    student = serializers.SerializerMethodField()

    class Meta:
        model = Enrollment
        fields = [
            "id", "course", "student", "status", "progress",
            "enrolled_at", "completed_at", "expiry_date", "is_reviewed",
        ]

    def get_student(self, obj):
        return {
            "id": obj.student.id,
            "first_name": obj.student.first_name,
            "last_name": obj.student.last_name,
            "profile_image": obj.student.profile_image.url if obj.student.profile_image else None,
        }


class EnrollmentCreateSerializer(serializers.Serializer):
    """Serializer for creating enrollments."""

    course_id = serializers.IntegerField()
    expiry_days = serializers.IntegerField(required=False, min_value=1)

    def validate_course_id(self, value):
        try:
            course = Course.objects.get(id=value)
            if course.status != Course.Status.PUBLISHED:
                raise serializers.ValidationError("Course is not available for enrollment.")
            return value
        except Course.DoesNotExist:
            raise serializers.ValidationError("Course not found.")


class WishlistSerializer(serializers.ModelSerializer):
    """Serializer for wishlist."""

    course = CourseListSerializer(read_only=True)

    class Meta:
        model = Wishlist
        fields = ["id", "course", "added_at"]


class BookmarkSerializer(serializers.ModelSerializer):
    """Serializer for bookmarks."""

    lesson_title = serializers.CharField(source="lesson.title", read_only=True)
    course_title = serializers.CharField(source="course.title", read_only=True)

    class Meta:
        model = Bookmark
        fields = ["id", "course_title", "lesson_title", "note", "created_at"]
