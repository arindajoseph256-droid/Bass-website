from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import UploadViewSet

router = DefaultRouter()
router.register("", UploadViewSet, basename="upload")

urlpatterns = [
    path("", include(router.urls)),
]
