from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import DashboardStatsView, CourseAnalyticsViewSet, UserActivityViewSet, RevenueReportView

router = DefaultRouter()
router.register("course-analytics", CourseAnalyticsViewSet, basename="course-analytics")
router.register("user-activity", UserActivityViewSet, basename="user-activity")

urlpatterns = [
    path("dashboard/", DashboardStatsView.as_view(), name="dashboard-stats"),
    path("revenue/", RevenueReportView.as_view(), name="revenue-report"),
    path("", include(router.urls)),
]
