from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated

from common.paginations import StandardResultsSetPagination
from .models import Notification, UserNotificationSettings
from .serializers import NotificationSerializer, UserNotificationSettingsSerializer


class NotificationViewSet(viewsets.ModelViewSet):
    """ViewSet for notifications."""

    serializer_class = NotificationSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return Notification.objects.filter(user=self.request.user)

    @action(detail=True, methods=["post"])
    def mark_read(self, request, pk=None):
        notification = self.get_object()
        notification.is_read = True
        notification.save()
        return Response({"success": True})

    @action(detail=False, methods=["post"])
    def mark_all_read(self, request):
        self.get_queryset().update(is_read=True)
        return Response({"success": True, "message": "All notifications marked as read."})

    @action(detail=False, methods=["get"])
    def unread_count(self, request):
        count = self.get_queryset().filter(is_read=False).count()
        return Response({"unread_count": count})


class UserNotificationSettingsViewSet(viewsets.ModelViewSet):
    """ViewSet for notification settings."""

    serializer_class = UserNotificationSettingsSerializer
    permission_classes = [IsAuthenticated]

    def get_queryset(self):
        return UserNotificationSettings.objects.filter(user=self.request.user)

    def perform_create(self, serializer):
        serializer.save(user=self.request.user)
