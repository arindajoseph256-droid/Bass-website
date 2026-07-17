from celery import shared_task
from django.utils import timezone
from datetime import timedelta


@shared_task
def cleanup_old_notifications():
    """Clean up old read notifications."""
    from .models import Notification
    
    cutoff = timezone.now() - timedelta(days=30)
    deleted, _ = Notification.objects.filter(
        is_read=True,
        created_at__lt=cutoff
    ).delete()
    
    return f"Cleaned up {deleted} old notifications"


@shared_task
def send_notification(user_id, notification_type, title, message, link=""):
    """Send a notification to a user."""
    from .models import Notification, UserNotificationSettings
    from django.contrib.auth import get_user_model
    
    User = get_user_model()
    
    try:
        user = User.objects.get(id=user_id)
        notification = Notification.objects.create(
            user=user,
            type=notification_type,
            title=title,
            message=message,
            link=link,
        )
        
        # Check if user wants email notifications
        try:
            settings = user.notification_settings
            should_email = (
                notification_type == "assignment" and settings.email_assignments or
                notification_type == "quiz" and settings.email_quizzes or
                notification_type == "grade" and settings.email_grades or
                notification_type == "course" and settings.email_course_updates or
                notification_type == "achievement" and settings.email_achievements
            )
            
            if should_email and settings.email_notifications:
                notification.is_email_sent = True
                notification.save()
                # Email sending would be handled here
                
        except UserNotificationSettings.DoesNotExist:
            pass
        
        return f"Notification sent to {user.email}"
        
    except User.DoesNotExist:
        return "User not found"
