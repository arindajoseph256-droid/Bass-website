from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import NotificationViewSet, UserNotificationSettingsViewSet

router = DefaultRouter()
router.register("", NotificationViewSet, basename="notification")
router.register("settings", UserNotificationSettingsViewSet, basename="notification-settings")

urlpatterns = [
    path("", include(router.urls)),
]
