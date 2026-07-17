from django.db import models
from django.contrib.auth import get_user_model

User = get_user_model()


class UploadedFile(models.Model):
    """Model for uploaded files."""

    class Type(models.TextChoices):
        IMAGE = "image", "Image"
        VIDEO = "video", "Video"
        AUDIO = "audio", "Audio"
        DOCUMENT = "document", "Document"
        OTHER = "other", "Other"

    uploaded_by = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="uploads",
    )
    file = models.FileField(upload_to="uploads/%Y/%m/")
    filename = models.CharField(max_length=255)
    file_size = models.BigIntegerField(default=0)
    mime_type = models.CharField(max_length=100)
    file_type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.OTHER,
    )
    is_public = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["uploaded_by", "-created_at"]),
            models.Index(fields=["file_type"]),
        ]

    def __str__(self):
        return self.filename
