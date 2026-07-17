from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SchoolViewSet, SchoolMembershipViewSet

router = DefaultRouter()
router.register("schools", SchoolViewSet, basename="school")

urlpatterns = [
    path("", include(router.urls)),
    path("schools/<int:school_id>/memberships/", SchoolMembershipViewSet.as_view(), name="school-memberships"),
]
