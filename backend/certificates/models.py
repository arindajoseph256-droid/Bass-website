from django.db import models
from django.contrib.auth import get_user_model
import uuid

User = get_user_model()


class CertificateTemplate(models.Model):
    """Template for certificates."""

    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    background_image = models.ImageField(upload_to="certificates/templates/")
    logo = models.ImageField(upload_to="certificates/logos/", blank=True)
    signature = models.ImageField(upload_to="certificates/signatures/", blank=True)
    signature_name = models.CharField(max_length=255, blank=True)
    signature_title = models.CharField(max_length=255, blank=True)
    is_default = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name


class Certificate(models.Model):
    """Student certificate model."""

    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="certificates",
    )
    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="certificates",
    )
    template = models.ForeignKey(
        CertificateTemplate,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="certificates",
    )
    
    # Certificate details
    certificate_id = models.UUIDField(default=uuid.uuid4, unique=True)
    title = models.CharField(max_length=255)
    student_name = models.CharField(max_length=255)
    course_name = models.CharField(max_length=255)
    teacher_name = models.CharField(max_length=255)
    completion_date = models.DateField()
    issue_date = models.DateField(auto_now_add=True)
    
    # Metadata
    grade = models.CharField(max_length=50, blank=True)
    duration_hours = models.IntegerField(default=0)
    skills = models.JSONField(default=list, blank=True)
    
    # PDF
    pdf_file = models.FileField(upload_to="certificates/pdfs/", blank=True)
    
    # Status
    is_verified = models.BooleanField(default=True)
    is_revoked = models.BooleanField(default=False)
    revoke_reason = models.TextField(blank=True)

    class Meta:
        ordering = ["-issue_date"]
        unique_together = ["student", "course"]
        indexes = [
            models.Index(fields=["certificate_id"]),
            models.Index(fields=["student", "course"]),
        ]

    def __str__(self):
        return f"{self.student_name} - {self.course_name}"

    @property
    def verification_url(self):
        return f"/verify/{self.certificate_id}/"
