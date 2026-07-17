from django.contrib import admin
from .models import Certificate, CertificateTemplate


@admin.register(CertificateTemplate)
class CertificateTemplateAdmin(admin.ModelAdmin):
    list_display = ["name", "is_default", "created_at"]


@admin.register(Certificate)
class CertificateAdmin(admin.ModelAdmin):
    list_display = ["certificate_id", "student", "course", "is_verified", "is_revoked", "issue_date"]
    list_filter = ["is_verified", "is_revoked", "issue_date"]
    search_fields = ["certificate_id", "student__email", "course__title", "student_name"]
    raw_id_fields = ["student", "course", "template"]
