from rest_framework import viewsets, generics, status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Count, Avg, Sum
from django.utils import timezone
from datetime import timedelta

from common.permissions import IsTeacherOrAdmin
from common.paginations import StandardResultsSetPagination
from courses.models import Course, Enrollment
from accounts.models import User
from .models import DailyStats, CourseAnalytics, UserActivity
from .serializers import DailyStatsSerializer, CourseAnalyticsSerializer, UserActivitySerializer


class DashboardStatsView(generics.GenericAPIView):
    """Get dashboard statistics."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        user = request.user
        
        if user.is_admin:
            return Response(self._get_admin_stats())
        elif user.is_teacher:
            return Response(self._get_teacher_stats(user))
        else:
            return Response(self._get_student_stats(user))

    def _get_admin_stats(self):
        today = timezone.now().date()
        week_ago = today - timedelta(days=7)
        
        return {
            "total_users": User.objects.count(),
            "active_users": User.objects.filter(last_activity__gte=week_ago).count(),
            "total_courses": Course.objects.filter(status=Course.Status.PUBLISHED).count(),
            "total_enrollments": Enrollment.objects.count(),
            "daily_stats": DailyStatsSerializer(
                DailyStats.objects.order_by("-date")[:7],
                many=True
            ).data,
        }

    def _get_teacher_stats(self, teacher):
        courses = Course.objects.filter(teacher=teacher)
        
        return {
            "total_courses": courses.count(),
            "published_courses": courses.filter(status=Course.Status.PUBLISHED).count(),
            "total_students": Enrollment.objects.filter(course__in=courses).values("student").distinct().count(),
            "total_earnings": sum(c.price * Enrollment.objects.filter(course=c).count() for c in courses),
            "recent_enrollments": Enrollment.objects.filter(
                course__in=courses
            ).select_related("student", "course").order_by("-enrolled_at")[:5],
        }

    def _get_student_stats(self, student):
        enrollments = Enrollment.objects.filter(student=student)
        
        return {
            "enrolled_courses": enrollments.count(),
            "completed_courses": enrollments.filter(status=Enrollment.Status.COMPLETED).count(),
            "in_progress": enrollments.filter(status=Enrollment.Status.ACTIVE).count(),
            "certificates": student.certificates.count(),
            "achievements": student.badges,
            "points": student.points,
        }


class CourseAnalyticsViewSet(viewsets.ModelViewSet):
    """ViewSet for course analytics."""

    serializer_class = CourseAnalyticsSerializer
    permission_classes = [IsTeacherOrAdmin]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        if self.request.user.is_admin:
            return CourseAnalytics.objects.all()
        return CourseAnalytics.objects.filter(course__teacher=self.request.user)


class UserActivityViewSet(viewsets.ModelViewSet):
    """ViewSet for user activity."""

    serializer_class = UserActivitySerializer
    permission_classes = [IsTeacherOrAdmin]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return UserActivity.objects.all().select_related("user")


class RevenueReportView(generics.GenericAPIView):
    """Get revenue report."""

    permission_classes = [IsTeacherOrAdmin]

    def get(self, request):
        courses = Course.objects.filter(
            teacher=request.user,
            status=Course.Status.PUBLISHED
        )
        
        data = []
        total_revenue = 0
        
        for course in courses:
            enrollments = Enrollment.objects.filter(course=course)
            revenue = float(course.price) * enrollments.count()
            total_revenue += revenue
            
            data.append({
                "course": course.title,
                "enrollments": enrollments.count(),
                "revenue": revenue,
            })
        
        return Response({
            "total_revenue": total_revenue,
            "courses": data,
        })
