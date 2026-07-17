from rest_framework import viewsets, generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.conf import settings
import qrcode
import io
import base64

from common.paginations import StandardResultsSetPagination
from common.permissions import IsTeacherOrAdmin
from courses.models import Course, Enrollment
from .models import Certificate, CertificateTemplate
from .serializers import (
    CertificateSerializer, CertificateDetailSerializer,
    CertificateTemplateSerializer, CertificateVerifySerializer,
)


class CertificateViewSet(viewsets.ModelViewSet):
    """ViewSet for certificates."""

    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        if self.request.user.is_teacher or self.request.user.is_admin:
            return Certificate.objects.filter(
                course__teacher=self.request.user
            ).select_related("student", "course")
        return Certificate.objects.filter(
            student=self.request.user
        ).select_related("course", "course__teacher")

    def get_serializer_class(self):
        if self.action == "retrieve":
            return CertificateDetailSerializer
        return CertificateSerializer

    @action(detail=False, methods=["post"])
    def generate(self, request):
        """Generate a certificate for course completion."""
        course_id = request.data.get("course_id")
        course = get_object_or_404(Course, id=course_id)
        
        # Check if user is enrolled
        enrollment = Enrollment.objects.filter(
            student=request.user, course=course,
            status=Enrollment.Status.COMPLETED
        ).first()
        
        if not enrollment:
            return Response({
                "success": False,
                "message": "You must complete the course first.",
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Check if certificate already exists
        existing = Certificate.objects.filter(student=request.user, course=course).first()
        if existing:
            return Response({
                "success": True,
                "certificate": CertificateSerializer(existing).data,
            })
        
        template = CertificateTemplate.objects.filter(is_default=True).first()
        
        certificate = Certificate.objects.create(
            student=request.user,
            course=course,
            template=template,
            title=f"Certificate of Completion - {course.title}",
            student_name=request.user.get_full_name(),
            course_name=course.title,
            teacher_name=course.teacher.get_full_name(),
            completion_date=enrollment.completed_at.date(),
            duration_hours=course.total_duration // 60,
        )
        
        return Response({
            "success": True,
            "certificate": CertificateSerializer(certificate).data,
        }, status=status.HTTP_201_CREATED)


class CertificateVerifyView(generics.RetrieveAPIView):
    """Verify a certificate."""

    permission_classes = [AllowAny]
    serializer_class = CertificateSerializer
    lookup_field = "certificate_id"

    def get(self, request, certificate_id):
        try:
            certificate = Certificate.objects.get(certificate_id=certificate_id)
            return Response({
                "success": True,
                "is_valid": not certificate.is_revoked,
                "certificate": CertificateSerializer(certificate).data,
            })
        except Certificate.DoesNotExist:
            return Response({
                "success": False,
                "is_valid": False,
                "message": "Certificate not found.",
            }, status=status.HTTP_404_NOT_FOUND)


class CertificateTemplateViewSet(viewsets.ModelViewSet):
    """ViewSet for certificate templates."""

    queryset = CertificateTemplate.objects.all()
    serializer_class = CertificateTemplateSerializer
    permission_classes = [IsTeacherOrAdmin]
