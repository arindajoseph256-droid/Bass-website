from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class Assignment(models.Model):
    """Course assignment model."""

    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="assignments",
    )
    lesson = models.ForeignKey(
        "lessons.Lesson",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="assignments",
    )
    title = models.CharField(max_length=255)
    description = models.TextField()
    instructions = models.TextField(blank=True)
    
    # Files
    attachment = models.FileField(upload_to="assignments/files/", blank=True)
    
    # Settings
    max_score = models.IntegerField(default=100)
    passing_score = models.IntegerField(
        default=60,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    allow_late_submission = models.BooleanField(default=True)
    late_penalty = models.IntegerField(
        default=10,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    max_attempts = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
    )
    is_active = models.BooleanField(default=True)
    
    # Dates
    available_from = models.DateTimeField(null=True, blank=True)
    due_date = models.DateTimeField()
    allow_submission_until = models.DateTimeField(null=True, blank=True)
    
    # Rubric
    rubric = models.JSONField(default=dict, blank=True)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-due_date"]
        indexes = [
            models.Index(fields=["course", "is_active"]),
            models.Index(fields=["due_date"]),
        ]

    def __str__(self):
        return f"{self.course.title} - {self.title}"

    @property
    def is_available(self):
        now = timezone.now()
        if self.available_from and now < self.available_from:
            return False
        if not self.is_active:
            return False
        return True

    @property
    def is_past_due(self):
        if self.allow_submission_until:
            return timezone.now() > self.allow_submission_until
        return timezone.now() > self.due_date

    @property
    def submissions_count(self):
        return self.submissions.count()


class Submission(models.Model):
    """Assignment submission model."""

    class Status(models.TextChoices):
        DRAFT = "draft", "Draft"
        SUBMITTED = "submitted", "Submitted"
        GRADED = "graded", "Graded"
        RETURNED = "returned", "Returned"

    assignment = models.ForeignKey(
        Assignment,
        on_delete=models.CASCADE,
        related_name="submissions",
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="assignment_submissions",
    )
    
    # Content
    content = models.TextField(blank=True)
    attachments = models.ManyToManyField(
        "uploads.UploadedFile",
        blank=True,
        related_name="assignment_submissions",
    )
    
    # Status
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.DRAFT,
    )
    
    # Grading
    score = models.IntegerField(null=True, blank=True)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, null=True, blank=True)
    is_passed = models.BooleanField(default=False)
    late_submission = models.BooleanField(default=False)
    late_penalty_applied = models.IntegerField(default=0)
    
    # Feedback
    feedback = models.TextField(blank=True)
    graded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="graded_submissions",
    )
    
    # Timestamps
    submitted_at = models.DateTimeField(null=True, blank=True)
    graded_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["assignment", "student"]
        ordering = ["-submitted_at"]
        indexes = [
            models.Index(fields=["assignment", "student"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.student} - {self.assignment.title}"

    def calculate_score(self):
        """Calculate score with late penalty if applicable."""
        if self.score is None:
            return None
        
        if self.late_submission and self.assignment.late_penalty > 0:
            penalty = int(self.score * self.assignment.late_penalty / 100)
            self.late_penalty_applied = penalty
            return self.score - penalty
        
        return self.score

    def check_passed(self):
        """Check if submission passed."""
        if self.score is None:
            return False
        return self.score >= self.assignment.passing_score

    @property
    def attempts_used(self):
        return 1  # Each submission counts as one attempt

    @property
    def can_resubmit(self):
        if self.status in [self.Status.DRAFT, self.Status.SUBMITTED]:
            return self.assignment.max_attempts > 1
        return False


class SubmissionAttachment(models.Model):
    """Additional attachments for submissions."""

    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        related_name="files",
    )
    file = models.FileField(upload_to="submissions/files/")
    filename = models.CharField(max_length=255)
    file_size = models.BigIntegerField(default=0)
    mime_type = models.CharField(max_length=100)
    uploaded_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.filename


class SubmissionComment(models.Model):
    """Comments on submissions."""

    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        related_name="comments",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="submission_comments",
    )
    content = models.TextField()
    is_private = models.BooleanField(default=False)  # Only visible to grader
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.user} on {self.submission}"


class AssignmentGrade(models.Model):
    """Detailed grade breakdown for assignments with rubrics."""

    submission = models.ForeignKey(
        Submission,
        on_delete=models.CASCADE,
        related_name="grade_breakdown",
    )
    criterion = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    max_points = models.IntegerField()
    points_earned = models.IntegerField(default=0)
    feedback = models.TextField(blank=True)

    class Meta:
        ordering = ["criterion"]

    def __str__(self):
        return f"{self.criterion}: {self.points_earned}/{self.max_points}"

    @property
    def percentage(self):
        if self.max_points > 0:
            return (self.points_earned / self.max_points) * 100
        return 0
