from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class School(models.Model):
    """School model."""

    name = models.CharField(max_length=255)
    slug = models.SlugField(max_length=255, unique=True)
    description = models.TextField(blank=True)
    logo = models.ImageField(upload_to="schools/logos/", blank=True)
    cover_image = models.ImageField(upload_to="schools/covers/", blank=True)
    
    # Contact
    website = models.URLField(blank=True)
    email = models.EmailField(blank=True)
    phone = models.CharField(max_length=20, blank=True)
    address = models.TextField(blank=True)
    
    # Admin
    admin = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_schools",
        limit_choices_to={"role__in": [User.Role.SCHOOL_ADMIN, User.Role.SYSTEM_ADMIN]},
    )
    
    # Settings
    is_active = models.BooleanField(default=True)
    max_teachers = models.IntegerField(default=100)
    max_students = models.IntegerField(default=1000)
    
    # Stats
    total_teachers = models.IntegerField(default=0)
    total_students = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["name"]
        indexes = [models.Index(fields=["slug"])]

    def __str__(self):
        return self.name


class SchoolMembership(models.Model):
    """School membership model."""

    class Role(models.TextChoices):
        TEACHER = "teacher", "Teacher"
        STUDENT = "student", "Student"

    school = models.ForeignKey(
        School,
        on_delete=models.CASCADE,
        related_name="memberships",
    )
    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="school_memberships",
    )
    role = models.CharField(max_length=20, choices=Role.choices)
    is_active = models.BooleanField(default=True)
    joined_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["school", "user"]
        indexes = [models.Index(fields=["school", "user", "role"])]

    def __str__(self):
        return f"{self.user} - {self.school.name} ({self.role})"
