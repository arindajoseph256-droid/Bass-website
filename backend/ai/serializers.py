from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import ChatSession, ChatMessage, GeneratedContent, AIActivity

User = get_user_model()


class ChatMessageSerializer(serializers.ModelSerializer):
    """Serializer for chat messages."""

    class Meta:
        model = ChatMessage
        fields = ["id", "role", "content", "tokens_used", "created_at"]
        read_only_fields = ["id", "tokens_used", "created_at"]


class ChatSessionSerializer(serializers.ModelSerializer):
    """Serializer for chat sessions."""

    messages = ChatMessageSerializer(many=True, read_only=True)
    last_message = serializers.SerializerMethodField()

    class Meta:
        model = ChatSession
        fields = [
            "id", "course", "title", "is_active",
            "messages", "last_message", "created_at", "updated_at",
        ]

    def get_last_message(self, obj):
        last = obj.messages.order_by("-created_at").first()
        if last:
            return {
                "content": last.content[:100],
                "role": last.role,
                "created_at": last.created_at,
            }
        return None


class ChatSessionCreateSerializer(serializers.Serializer):
    """Serializer for creating a chat session."""

    course_id = serializers.IntegerField(required=False, allow_null=True)
    title = serializers.CharField(max_length=255, required=False, allow_blank=True)
    message = serializers.CharField(required=True)


class SendMessageSerializer(serializers.Serializer):
    """Serializer for sending a chat message."""

    message = serializers.CharField(required=True)
    session_id = serializers.IntegerField(required=False)


class GenerateQuestionsSerializer(serializers.Serializer):
    """Serializer for generating practice questions."""

    topic = serializers.CharField(required=True)
    count = serializers.IntegerField(min_value=1, max_value=20, default=5)
    question_type = serializers.ChoiceField(
        choices=["multiple_choice", "true_false", "fill_blank"],
        default="multiple_choice",
    )
    course_id = serializers.IntegerField(required=False)
    lesson_id = serializers.IntegerField(required=False)


class GenerateFlashcardsSerializer(serializers.Serializer):
    """Serializer for generating flashcards."""

    text = serializers.CharField(required=True)
    count = serializers.IntegerField(min_value=1, max_value=20, default=10)
    course_id = serializers.IntegerField(required=False)
    lesson_id = serializers.IntegerField(required=False)


class SummarizeTextSerializer(serializers.Serializer):
    """Serializer for summarizing text."""

    text = serializers.CharField(required=True)
    max_length = serializers.IntegerField(min_value=50, max_value=500, default=200)
    course_id = serializers.IntegerField(required=False)
    lesson_id = serializers.IntegerField(required=False)


class ExplainTopicSerializer(serializers.Serializer):
    """Serializer for explaining a topic."""

    topic = serializers.CharField(required=True)
    context = serializers.CharField(required=False, allow_blank=True, default="")
    course_id = serializers.IntegerField(required=False)
    lesson_id = serializers.IntegerField(required=False)


class GrammarCheckSerializer(serializers.Serializer):
    """Serializer for grammar checking."""

    text = serializers.CharField(required=True)


class StudyPlanSerializer(serializers.Serializer):
    """Serializer for generating a study plan."""

    topic = serializers.CharField(required=True)
    duration_days = serializers.IntegerField(min_value=1, max_value=30, default=7)
    course_id = serializers.IntegerField(required=False)


class GeneratedContentSerializer(serializers.ModelSerializer):
    """Serializer for generated content."""

    generated_by_name = serializers.SerializerMethodField()

    class Meta:
        model = GeneratedContent
        fields = [
            "id", "course", "lesson", "content_type", "title",
            "content", "generated_by_name", "created_at",
        ]

    def get_generated_by_name(self, obj):
        if obj.generated_by:
            return obj.generated_by.get_full_name()
        return None


class AIActivitySerializer(serializers.ModelSerializer):
    """Serializer for AI activity logs."""

    user_name = serializers.SerializerMethodField()

    class Meta:
        model = AIActivity
        fields = ["id", "user", "user_name", "activity_type", "tokens_used", "response_time", "created_at"]

    def get_user_name(self, obj):
        return obj.user.get_full_name()
