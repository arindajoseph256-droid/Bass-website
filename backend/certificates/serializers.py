from rest_framework import serializers
from .models import Certificate, CertificateTemplate


class CertificateTemplateSerializer(serializers.ModelSerializer):
    class Meta:
        model = CertificateTemplate
        fields = "__all__"


class CertificateSerializer(serializers.ModelSerializer):
    verification_url = serializers.CharField(read_only=True)

    class Meta:
        model = Certificate
        fields = [
            "id", "certificate_id", "title", "student_name",
            "course_name", "teacher_name", "completion_date",
            "issue_date", "grade", "duration_hours", "skills",
            "is_verified", "is_revoked", "verification_url",
        ]


class CertificateDetailSerializer(CertificateSerializer):
    template = CertificateTemplateSerializer()

    class Meta(CertificateSerializer.Meta):
        fields = CertificateSerializer.Meta.fields + ["template", "pdf_file"]


class CertificateVerifySerializer(serializers.Serializer):
    certificate_id = serializers.UUIDField()
