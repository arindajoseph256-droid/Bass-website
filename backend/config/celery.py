import os
from celery import Celery
from celery.schedules import crontab

os.environ.setdefault("DJANGO_SETTINGS_MODULE", "config.settings")

app = Celery("edushare")
app.config_from_object("django.conf:settings", namespace="CELERY")
app.autodiscover_tasks()

# Celery Beat Schedule
app.conf.beat_schedule = {
    "cleanup-expired-tokens": {
        "task": "accounts.tasks.cleanup_expired_tokens",
        "schedule": crontab(hour=0, minute=0),
    },
    "send-course-reminders": {
        "task": "courses.tasks.send_course_reminders",
        "schedule": crontab(hour=9, minute=0),
    },
    "generate-daily-analytics": {
        "task": "analytics.tasks.generate_daily_analytics",
        "schedule": crontab(hour=1, minute=0),
    },
    "cleanup-old-notifications": {
        "task": "notifications.tasks.cleanup_old_notifications",
        "schedule": crontab(hour=2, minute=0),
    },
}


@app.task(bind=True, ignore_result=True)
def debug_task(self):
    print(f"Request: {self.request!r}")
