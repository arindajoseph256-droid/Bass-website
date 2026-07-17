import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from notifications.models import Notification, UserNotificationSettings
from unittest.mock import patch

User = get_user_model()


@pytest.mark.django_db
class TestNotifications:
    def test_notification_creation(self, student_user):
        """Test that notifications can be created."""
        notification = Notification.objects.create(
            user=student_user,
            type=Notification.Type.ASSIGNMENT,
            title="Test Assignment",
            message="You have a new assignment",
        )
        assert notification.id is not None
        assert notification.is_read is False

    def test_notification_settings(self, student_user):
        """Test that notification settings can be created and accessed."""
        settings, created = UserNotificationSettings.objects.get_or_create(user=student_user)
        assert settings.user == student_user
        assert settings.email_assignments is True  # Default value

    def test_notification_list_api(self, authenticated_client, student_user):
        """Test listing notifications via API."""
        Notification.objects.create(
            user=student_user,
            type=Notification.Type.COURSE,
            title="Test Notification",
            message="Test message",
        )
        
        response = authenticated_client.get("/api/notifications/")
        assert response.status_code == status.HTTP_200_OK
