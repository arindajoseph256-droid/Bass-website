from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class DailyStats(models.Model):
    """Daily platform statistics."""

    date = models.DateField(unique=True)
    total_users = models.IntegerField(default=0)
    active_users = models.IntegerField(default=0)
    new_registrations = models.IntegerField(default=0)
    total_courses = models.IntegerField(default=0)
    total_enrollments = models.IntegerField(default=0)
    total_completions = models.IntegerField(default=0)
    total_revenue = models.DecimalField(max_digits=12, decimal_places=2, default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-date"]
        verbose_name_plural = "Daily Stats"

    def __str__(self):
        return str(self.date)


class CourseAnalytics(models.Model):
    """Per-course analytics."""

    course = models.OneToOneField(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="analytics",
    )
    views = models.IntegerField(default=0)
    unique_views = models.IntegerField(default=0)
    enrollments = models.IntegerField(default=0)
    completions = models.IntegerField(default=0)
    average_progress = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    average_rating = models.DecimalField(max_digits=3, decimal_places=2, default=0)
    completion_rate = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"Analytics for {self.course.title}"


class UserActivity(models.Model):
    """Track user activity."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="activities",
    )
    activity_type = models.CharField(max_length=50)
    resource_type = models.CharField(max_length=50, blank=True)
    resource_id = models.IntegerField(null=True, blank=True)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "activity_type"]),
            models.Index(fields=["created_at"]),
        ]

    def __str__(self):
        return f"{self.user} - {self.activity_type}"
