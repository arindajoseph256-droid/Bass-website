from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Chapter(models.Model):
    """Course chapter model."""

    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="chapters",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["order", "title"]
        unique_together = ["course", "title"]

    def __str__(self):
        return f"{self.course.title} - {self.title}"

    @property
    def total_lessons(self):
        return self.lessons.count()

    @property
    def total_duration(self):
        return sum(lesson.duration for lesson in self.lessons.all())


class Lesson(models.Model):
    """Lesson model for course content."""

    class Type(models.TextChoices):
        VIDEO = "video", "Video"
        PDF = "pdf", "PDF"
        TEXT = "text", "Text"
        QUIZ = "quiz", "Quiz"
        ASSIGNMENT = "assignment", "Assignment"
        LIVE = "live", "Live Session"

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        PUBLISHED = "published", "Published"
        SCHEDULED = "scheduled", "Scheduled"

    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="lessons",
    )
    chapter = models.ForeignKey(
        Chapter,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="lessons",
    )
    title = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255)
    description = models.TextField(blank=True)
    type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.VIDEO,
    )
    content = models.TextField(blank=True)  # For text lessons

    # Media
    video_url = models.URLField(blank=True)
    video_file = models.FileField(upload_to="lessons/videos/", blank=True)
    video_duration = models.IntegerField(default=0)  # in seconds
    pdf_file = models.FileField(upload_to="lessons/pdfs/", blank=True)
    thumbnail = models.ImageField(upload_to="lessons/thumbnails/", blank=True)

    # Settings
    is_free_preview = models.BooleanField(default=False)
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    order = models.IntegerField(default=0)
    duration = models.IntegerField(default=0)  # in minutes

    # Completion tracking
    is_completed = models.BooleanField(default=False)

    # Live session settings
    live_url = models.URLField(blank=True)
    scheduled_at = models.DateTimeField(null=True, blank=True)

    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    published_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["course", "chapter", "order", "title"]
        indexes = [
            models.Index(fields=["course", "status"]),
            models.Index(fields=["chapter", "order"]),
            models.Index(fields=["slug"]),
        ]

    def __str__(self):
        return f"{self.course.title} - {self.title}"

    @property
    def duration_formatted(self):
        minutes = self.duration
        hours = minutes // 60
        minutes = minutes % 60
        if hours > 0:
            return f"{hours}h {minutes}m"
        return f"{minutes}m"

    @property
    def video_duration_formatted(self):
        seconds = self.video_duration
        minutes = seconds // 60
        seconds = seconds % 60
        return f"{minutes:02d}:{seconds:02d}"


class LessonProgress(models.Model):
    """Track student progress in lessons."""

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="lesson_progress",
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="progress_records",
    )
    is_completed = models.BooleanField(default=False)
    watched_duration = models.IntegerField(default=0)  # in seconds
    last_position = models.IntegerField(default=0)  # video last position
    completed_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["student", "lesson"]
        ordering = ["-updated_at"]

    def __str__(self):
        return f"{self.student} - {self.lesson.title}"


class LessonResource(models.Model):
    """Additional resources for lessons."""

    class Type(models.TextChoices):
        FILE = "file", "File"
        LINK = "link", "Link"
        CODE = "code", "Code Snippet"

    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="resources",
    )
    title = models.CharField(max_length=255)
    type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.FILE,
    )
    file = models.FileField(upload_to="lessons/resources/", blank=True)
    url = models.URLField(blank=True)
    content = models.TextField(blank=True)  # For code snippets
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "title"]

    def __str__(self):
        return f"{self.lesson.title} - {self.title}"


class LessonNote(models.Model):
    """Student notes for lessons."""

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="lesson_notes",
    )
    lesson = models.ForeignKey(
        Lesson,
        on_delete=models.CASCADE,
        related_name="notes",
    )
    content = models.TextField()
    timestamp = models.IntegerField(default=0)  # Video timestamp in seconds
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-timestamp", "-created_at"]
        unique_together = ["student", "lesson", "timestamp"]

    def __str__(self):
        return f"{self.student} - {self.lesson.title} @ {self.timestamp}s"
