from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Chapter, Lesson, LessonProgress, LessonResource, LessonNote

User = get_user_model()


class LessonResourceSerializer(serializers.ModelSerializer):
    """Serializer for lesson resources."""

    class Meta:
        model = LessonResource
        fields = ["id", "title", "type", "file", "url", "content", "order"]


class LessonListSerializer(serializers.ModelSerializer):
    """Serializer for lesson list view."""

    chapter_title = serializers.CharField(source="chapter.title", read_only=True, allow_null=True)
    is_completed = serializers.SerializerMethodField()
    progress = serializers.SerializerMethodField()

    class Meta:
        model = Lesson
        fields = [
            "id", "title", "slug", "chapter_title", "type",
            "duration", "duration_formatted", "video_duration_formatted",
            "thumbnail", "is_free_preview", "order", "status",
            "is_completed", "progress", "published_at",
        ]

    def get_is_completed(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return LessonProgress.objects.filter(
                student=request.user, lesson=obj, is_completed=True
            ).exists()
        return False

    def get_progress(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            progress = LessonProgress.objects.filter(
                student=request.user, lesson=obj
            ).first()
            if progress:
                return {
                    "watched_duration": progress.watched_duration,
                    "last_position": progress.last_position,
                    "is_completed": progress.is_completed,
                }
        return None


class LessonDetailSerializer(LessonListSerializer):
    """Serializer for lesson detail view."""

    resources = LessonResourceSerializer(many=True, read_only=True)
    notes_count = serializers.SerializerMethodField()

    class Meta(LessonListSerializer.Meta):
        fields = LessonListSerializer.Meta.fields + [
            "description", "content", "video_url", "video_file",
            "pdf_file", "live_url", "scheduled_at", "resources",
            "notes_count", "created_at", "updated_at",
        ]

    def get_notes_count(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.notes.filter(student=request.user).count()
        return 0


class LessonCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating lessons."""

    class Meta:
        model = Lesson
        fields = [
            "title", "slug", "description", "chapter", "type",
            "content", "video_url", "video_file", "video_duration",
            "pdf_file", "thumbnail", "is_free_preview", "status",
            "order", "duration", "live_url", "scheduled_at",
        ]


class ChapterSerializer(serializers.ModelSerializer):
    """Serializer for chapters."""

    lessons = LessonListSerializer(many=True, read_only=True)
    total_lessons = serializers.IntegerField()
    total_duration = serializers.IntegerField()

    class Meta:
        model = Chapter
        fields = [
            "id", "title", "description", "order",
            "total_lessons", "total_duration", "lessons",
        ]


class ChapterCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating chapters."""

    class Meta:
        model = Chapter
        fields = ["title", "description", "order", "course"]


class LessonProgressSerializer(serializers.ModelSerializer):
    """Serializer for lesson progress."""

    lesson_title = serializers.CharField(source="lesson.title", read_only=True)
    course_title = serializers.CharField(source="lesson.course.title", read_only=True)

    class Meta:
        model = LessonProgress
        fields = [
            "id", "lesson", "lesson_title", "course_title",
            "is_completed", "watched_duration", "last_position",
            "completed_at", "created_at", "updated_at",
        ]


class LessonNoteSerializer(serializers.ModelSerializer):
    """Serializer for lesson notes."""

    class Meta:
        model = LessonNote
        fields = ["id", "lesson", "content", "timestamp", "created_at", "updated_at"]

    def create(self, validated_data):
        lesson_id = validated_data.get("lesson").id
        timestamp = validated_data.get("timestamp", 0)
        
        # Check if note exists at same timestamp
        existing = LessonNote.objects.filter(
            student=validated_data["student"],
            lesson_id=lesson_id,
            timestamp=timestamp,
        ).first()
        
        if existing:
            existing.content = validated_data["content"]
            existing.save()
            return existing
        
        return super().create(validated_data)
