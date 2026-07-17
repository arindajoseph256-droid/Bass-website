from celery import shared_task
from django.utils import timezone
from datetime import timedelta


@shared_task
def cleanup_expired_tokens():
    """Clean up expired user sessions and tokens."""
    from .models import UserSession
    
    # Delete expired sessions
    expired_sessions = UserSession.objects.filter(
        expires_at__lt=timezone.now(),
        is_active=True
    )
    count = expired_sessions.count()
    expired_sessions.update(is_active=False)
    
    return f"Cleaned up {count} expired sessions"


@shared_task
def send_welcome_email(user_id):
    """Send welcome email to new users."""
    from django.conf import settings
    from django.core.mail import send_mail
    
    from .models import User
    
    try:
        user = User.objects.get(id=user_id)
        send_mail(
            subject=f"Welcome to EduShare AI, {user.first_name}!",
            message=f"Hi {user.first_name},\n\nWelcome to EduShare AI Learning Management System. We're excited to have you!\n\nBest regards,\nThe EduShare Team",
            from_email=settings.DEFAULT_FROM_EMAIL,
            recipient_list=[user.email],
            fail_silently=True,
        )
        return f"Welcome email sent to {user.email}"
    except Exception as e:
        return f"Failed to send welcome email: {str(e)}"
