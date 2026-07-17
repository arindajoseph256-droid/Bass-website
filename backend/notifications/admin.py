from django.contrib import admin
from .models import Notification, UserNotificationSettings


@admin.register(Notification)
class NotificationAdmin(admin.ModelAdmin):
    list_display = ["user", "type", "title", "is_read", "created_at"]
    list_filter = ["type", "is_read", "created_at"]
    search_fields = ["title", "message", "user__email"]
    raw_id_fields = ["user"]


@admin.register(UserNotificationSettings)
class UserNotificationSettingsAdmin(admin.ModelAdmin):
    list_display = ["user", "email_assignments", "email_quizzes", "push_notifications"]
    search_fields = ["user__email"]
    raw_id_fields = ["user"]
