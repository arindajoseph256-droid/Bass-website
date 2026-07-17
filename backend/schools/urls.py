from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import SchoolViewSet, SchoolMembershipViewSet

router = DefaultRouter()
router.register("schools", SchoolViewSet, basename="school")
router.register("memberships", SchoolMembershipViewSet, basename="school-membership")

urlpatterns = [
    path("", include(router.urls)),
]
