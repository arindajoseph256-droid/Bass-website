from django.contrib import admin
from .models import DailyStats, CourseAnalytics, UserActivity


@admin.register(DailyStats)
class DailyStatsAdmin(admin.ModelAdmin):
    list_display = ["date", "total_users", "active_users", "total_courses", "total_enrollments"]
    list_filter = ["date"]
    date_hierarchy = "date"


@admin.register(CourseAnalytics)
class CourseAnalyticsAdmin(admin.ModelAdmin):
    list_display = ["course", "views", "enrollments", "completions", "completion_rate"]
    search_fields = ["course__title"]


@admin.register(UserActivity)
class UserActivityAdmin(admin.ModelAdmin):
    list_display = ["user", "activity_type", "resource_type", "created_at"]
    list_filter = ["activity_type", "created_at"]
    search_fields = ["user__email"]
