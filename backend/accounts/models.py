from django.contrib.auth.models import AbstractUser, BaseUserManager, Permission, Group
from django.contrib.postgres.fields import ArrayField
from django.db import models
from django.utils import timezone
from django.utils.translation import gettext_lazy as _


class UserManager(BaseUserManager):
    """Custom user manager for email-based authentication."""

    def create_user(self, email, password=None, **extra_fields):
        if not email:
            raise ValueError("The Email field must be set")
        email = self.normalize_email(email)
        user = self.model(email=email, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_superuser(self, email, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        extra_fields.setdefault("is_active", True)
        extra_fields.setdefault("role", User.Role.SYSTEM_ADMIN)

        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")

        return self.create_user(email, password, **extra_fields)


class User(AbstractUser):
    """Custom User model with role-based access control."""

    class Role(models.TextChoices):
        GUEST = "guest", _("Guest")
        STUDENT = "student", _("Student")
        TEACHER = "teacher", _("Teacher")
        SCHOOL_ADMIN = "school_admin", _("School Administrator")
        SYSTEM_ADMIN = "system_admin", _("System Administrator")
        MODERATOR = "moderator", _("Moderator")

    class Gender(models.TextChoices):
        MALE = "male", _("Male")
        FEMALE = "female", _("Female")
        OTHER = "other", _("Other")
        PREFER_NOT_TO_SAY = "not_specified", _("Prefer not to say")

    username = models.CharField(
        max_length=150,
        unique=True,
        blank=True,
        null=True,
        help_text=_("Required. 150 characters or fewer."),
    )
    email = models.EmailField(_("email address"), unique=True)
    role = models.CharField(
        max_length=20,
        choices=Role.choices,
        default=Role.STUDENT,
        db_index=True,
    )
    gender = models.CharField(
        max_length=20,
        choices=Gender.choices,
        default=Gender.PREFER_NOT_TO_SAY,
    )
    phone = models.CharField(max_length=20, blank=True, null=True)
    bio = models.TextField(blank=True, max_length=500)
    date_of_birth = models.DateField(blank=True, null=True)
    profile_image = models.ImageField(
        upload_to="profiles/",
        default="defaults/avatar.png",
        blank=True,
    )
    cover_image = models.ImageField(
        upload_to="covers/",
        blank=True,
        null=True,
    )
    address = models.TextField(blank=True)
    city = models.CharField(max_length=100, blank=True)
    country = models.CharField(max_length=100, blank=True)
    postal_code = models.CharField(max_length=20, blank=True)

    # Status fields
    is_verified = models.BooleanField(default=False)
    verification_token = models.CharField(max_length=255, blank=True)
    password_reset_token = models.CharField(max_length=255, blank=True)
    password_reset_token_expires = models.DateTimeField(blank=True, null=True)

    # Social links
    website = models.URLField(blank=True)
    linkedin = models.URLField(blank=True)
    twitter = models.URLField(blank=True)
    github = models.URLField(blank=True)

    # Notification preferences
    email_notifications = models.BooleanField(default=True)
    push_notifications = models.BooleanField(default=True)

    # Preferences
    language = models.CharField(max_length=10, default="en")
    timezone = models.CharField(max_length=50, default="UTC")
    dark_mode = models.BooleanField(default=False)

    # Achievement fields
    badges = ArrayField(models.CharField(max_length=50), default=list, blank=True)
    points = models.IntegerField(default=0)

    # Privacy
    is_public = models.BooleanField(default=True)
    show_email = models.BooleanField(default=False)
    show_profile = models.BooleanField(default=True)

    # Timestamps
    last_activity = models.DateTimeField(blank=True, null=True)
    last_login_ip = models.GenericIPAddressField(blank=True, null=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["first_name", "last_name"]

    objects = UserManager()

    class Meta:
        verbose_name = _("user")
        verbose_name_plural = _("users")
        ordering = ["-date_joined"]
        indexes = [
            models.Index(fields=["email"]),
            models.Index(fields=["role"]),
            models.Index(fields=["is_verified"]),
            models.Index(fields=["-points"]),
        ]

    def __str__(self):
        return self.get_full_name() or self.email

    @property
    def is_admin(self):
        return self.role == self.Role.SYSTEM_ADMIN or self.is_superuser

    @property
    def is_teacher(self):
        return self.role in [self.Role.TEACHER, self.Role.SCHOOL_ADMIN]

    @property
    def is_student(self):
        return self.role == self.Role.STUDENT

    @property
    def is_school_admin(self):
        return self.role == self.Role.SCHOOL_ADMIN

    @property
    def is_moderator(self):
        return self.role == self.Role.MODERATOR or self.is_admin

    @property
    def is_guest(self):
        return self.role == self.Role.GUEST

    def get_full_name(self):
        full_name = f"{self.first_name} {self.last_name}".strip()
        return full_name or self.email.split("@")[0]

    def add_badge(self, badge):
        if badge not in self.badges:
            self.badges.append(badge)
            self.save(update_fields=["badges"])

    def add_points(self, points):
        self.points += points
        self.save(update_fields=["points"])

    def update_last_activity(self):
        self.last_activity = timezone.now()
        self.save(update_fields=["last_activity"])

    def save(self, *args, **kwargs):
        if not self.username:
            self.username = self.email.split("@")[0]
        super().save(*args, **kwargs)


class UserSession(models.Model):
    """Track user login sessions."""

    user = models.ForeignKey(User, on_delete=models.CASCADE, related_name="sessions")
    token = models.CharField(max_length=500, unique=True)
    ip_address = models.GenericIPAddressField(blank=True, null=True)
    user_agent = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()
    is_active = models.BooleanField(default=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["user", "is_active"]),
            models.Index(fields=["token"]),
        ]

    def __str__(self):
        return f"{self.user.email} - {self.created_at}"
