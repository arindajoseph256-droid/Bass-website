from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class ChatSession(models.Model):
    """AI tutor chat session."""

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="ai_sessions",
    )
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ai_sessions",
    )
    title = models.CharField(max_length=255, blank=True)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [
            models.Index(fields=["student", "is_active"]),
        ]

    def __str__(self):
        return f"{self.student} - {self.title or 'Chat'}"


class ChatMessage(models.Model):
    """Individual message in a chat session."""

    class Role(models.TextChoices):
        USER = "user", "User"
        ASSISTANT = "assistant", "Assistant"
        SYSTEM = "system", "System"

    session = models.ForeignKey(
        ChatSession,
        on_delete=models.CASCADE,
        related_name="messages",
    )
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.USER,
    )
    content = models.TextField()
    tokens_used = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.role}: {self.content[:50]}..."


class GeneratedContent(models.Model):
    """Track AI-generated content for a course."""

    class ContentType(models.TextChoices):
        QUESTIONS = "questions", "Practice Questions"
        FLASHCARDS = "flashcards", "Flashcards"
        SUMMARY = "summary", "Summary"
        EXPLANATION = "explanation", "Topic Explanation"
        STUDY_PLAN = "study_plan", "Study Plan"
        QUIZ = "quiz", "AI-Generated Quiz"

    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="ai_content",
    )
    lesson = models.ForeignKey(
        "lessons.Lesson",
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="ai_content",
    )
    content_type = models.CharField(
        max_length=20,
        choices=ContentType.choices,
    )
    title = models.CharField(max_length=255)
    content = models.JSONField(default=dict)
    generated_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        related_name="generated_content",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.content_type}: {self.title}"


class AIActivity(models.Model):
    """Track AI usage activity for analytics."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="ai_activities",
    )
    activity_type = models.CharField(max_length=50)
    tokens_used = models.IntegerField(default=0)
    response_time = models.IntegerField(default=0)  # in milliseconds
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        verbose_name_plural = "AI Activities"
