from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class Notification(models.Model):
    """User notification model."""

    class Type(models.TextChoices):
        ASSIGNMENT = "assignment", "Assignment"
        QUIZ = "quiz", "Quiz"
        COURSE = "course", "Course"
        GRADE = "grade", "Grade"
        FORUM = "forum", "Forum"
        SYSTEM = "system", "System"
        ACHIEVEMENT = "achievement", "Achievement"

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="notifications",
    )
    type = models.CharField(max_length=20, choices=Type.choices, default=Type.SYSTEM)
    title = models.CharField(max_length=255)
    message = models.TextField()
    link = models.CharField(max_length=500, blank=True)
    is_read = models.BooleanField(default=False)
    is_email_sent = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_read", "-created_at"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.title}"


class UserNotificationSettings(models.Model):
    """User notification preferences."""

    user = models.OneToOneField(
        User,
        on_delete=models.CASCADE,
        related_name="notification_settings",
    )
    email_assignments = models.BooleanField(default=True)
    email_quizzes = models.BooleanField(default=True)
    email_grades = models.BooleanField(default=True)
    email_course_updates = models.BooleanField(default=True)
    email_forum_replies = models.BooleanField(default=True)
    email_achievements = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)
    browser_notifications = models.BooleanField(default=False)

    def __str__(self):
        return f"Settings for {self.user}"
