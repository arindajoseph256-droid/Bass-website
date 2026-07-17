from celery import shared_task
from django.utils import timezone
from datetime import timedelta


@shared_task
def generate_daily_analytics():
    """Generate daily analytics snapshot."""
    from .models import DailyStats, CourseAnalytics
    from courses.models import Course, Enrollment
    from accounts.models import User
    
    today = timezone.now().date()
    
    # Check if already exists
    if DailyStats.objects.filter(date=today).exists():
        return "Already generated"
    
    # Calculate stats
    active_start = today - timedelta(days=1)
    
    stats = DailyStats.objects.create(
        date=today,
        total_users=User.objects.count(),
        active_users=User.objects.filter(last_activity__gte=active_start).count(),
        new_registrations=User.objects.filter(date_joined__date=today).count(),
        total_courses=Course.objects.filter(status=Course.Status.PUBLISHED).count(),
        total_enrollments=Enrollment.objects.count(),
        total_completions=Enrollment.objects.filter(status=Enrollment.Status.COMPLETED).count(),
    )
    
    return f"Generated stats for {today}"
