from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import CertificateViewSet, CertificateVerifyView, CertificateTemplateViewSet

router = DefaultRouter()
router.register("", CertificateViewSet, basename="certificate")
router.register("templates", CertificateTemplateViewSet, basename="certificate-template")

urlpatterns = [
    path("verify/<uuid:certificate_id>/", CertificateVerifyView.as_view(), name="verify"),
    path("", include(router.urls)),
]
