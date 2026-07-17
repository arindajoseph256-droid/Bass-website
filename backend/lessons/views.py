from rest_framework import viewsets, generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404
from django.utils import timezone

from courses.models import Course, Enrollment
from common.permissions import IsTeacherOrAdmin, IsEnrolledStudentOrTeacher
from common.paginations import StandardResultsSetPagination
from .models import Chapter, Lesson, LessonProgress, LessonResource, LessonNote
from .serializers import (
    ChapterSerializer, ChapterCreateUpdateSerializer,
    LessonListSerializer, LessonDetailSerializer,
    LessonCreateUpdateSerializer, LessonProgressSerializer,
    LessonNoteSerializer,
)


class ChapterViewSet(viewsets.ModelViewSet):
    """ViewSet for chapters."""

    serializer_class = ChapterSerializer
    permission_classes = [IsTeacherOrAdmin]
    pagination_class = None

    def get_queryset(self):
        course_id = self.kwargs.get("course_id")
        return Chapter.objects.filter(course_id=course_id).prefetch_related("lessons")

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return ChapterCreateUpdateSerializer
        return ChapterSerializer

    def perform_create(self, serializer):
        course_id = self.kwargs.get("course_id")
        course = Course.objects.get(id=course_id)
        
        # Check if user is the course teacher
        if course.teacher != self.request.user and not self.request.user.is_admin:
            raise PermissionError("You don't have permission to add chapters to this course.")
        
        serializer.save(course=course)


class LessonViewSet(viewsets.ModelViewSet):
    """ViewSet for lessons."""

    serializer_class = LessonListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination
    lookup_field = "slug"

    def get_queryset(self):
        course_id = self.kwargs.get("course_id")
        queryset = Lesson.objects.filter(course_id=course_id)
        
        if self.action == "list":
            # Only show published lessons to students
            if not (self.request.user.is_teacher or self.request.user.is_admin):
                queryset = queryset.filter(status=Lesson.Status.PUBLISHED)
        
        return queryset.select_related("chapter", "course")

    def get_serializer_class(self):
        if self.action == "retrieve":
            return LessonDetailSerializer
        if self.action in ["create", "update", "partial_update"]:
            return LessonCreateUpdateSerializer
        return LessonListSerializer

    def get_permissions(self):
        if self.action == "retrieve":
            return [IsAuthenticated()]
        return [IsTeacherOrAdmin()]

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        course = instance.course
        
        # Check enrollment for non-preview lessons
        if not instance.is_free_preview:
            if not request.user.is_teacher and not request.user.is_admin:
                if course.teacher != request.user:
                    enrollment = Enrollment.objects.filter(
                        student=request.user, course=course
                    ).exists()
                    if not enrollment:
                        return Response({
                            "success": False,
                            "message": "You must be enrolled to access this lesson.",
                        }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = self.get_serializer(instance)
        return Response({
            "success": True,
            "lesson": serializer.data,
        })

    def perform_create(self, serializer):
        course_id = self.kwargs.get("course_id")
        course = Course.objects.get(id=course_id)
        
        if course.teacher != self.request.user and not self.request.user.is_admin:
            raise PermissionError("You don't have permission to add lessons to this course.")
        
        lesson = serializer.save(course=course)
        
        # Update course total lessons
        course.total_lessons = course.lessons.count()
        course.save(update_fields=["total_lessons"])

    @action(detail=True, methods=["post"])
    def complete(self, request, course_id=None, slug=None):
        """Mark lesson as completed."""
        lesson = self.get_object()
        
        progress, created = LessonProgress.objects.get_or_create(
            student=request.user,
            lesson=lesson,
            defaults={"is_completed": True, "completed_at": timezone.now()},
        )
        
        if not created:
            progress.is_completed = True
            progress.completed_at = timezone.now()
            progress.save()
        
        # Update course progress
        self._update_course_progress(lesson.course, request.user)
        
        return Response({
            "success": True,
            "message": "Lesson marked as completed.",
        })

    @action(detail=True, methods=["post"])
    def update_progress(self, request, course_id=None, slug=None):
        """Update video watching progress."""
        lesson = self.get_object()
        watched_duration = request.data.get("watched_duration", 0)
        last_position = request.data.get("last_position", 0)
        
        progress, created = LessonProgress.objects.get_or_create(
            student=request.user,
            lesson=lesson,
        )
        
        progress.watched_duration = max(progress.watched_duration, watched_duration)
        progress.last_position = last_position
        
        # Auto-complete if watched 90% of video
        if lesson.video_duration > 0:
            watch_percentage = (watched_duration / lesson.video_duration) * 100
            if watch_percentage >= 90:
                progress.is_completed = True
                progress.completed_at = timezone.now()
        
        progress.save()
        
        return Response({
            "success": True,
            "progress": LessonProgressSerializer(progress).data,
        })

    def _update_course_progress(self, course, student):
        """Update overall course progress."""
        try:
            enrollment = Enrollment.objects.get(student=student, course=course)
            total_lessons = course.lessons.count()
            
            if total_lessons > 0:
                completed = LessonProgress.objects.filter(
                    student=student,
                    lesson__course=course,
                    is_completed=True,
                ).count()
                progress = int((completed / total_lessons) * 100)
                
                enrollment.progress = progress
                if progress >= 100:
                    enrollment.status = Enrollment.Status.COMPLETED
                    enrollment.completed_at = timezone.now()
                enrollment.save(update_fields=["progress", "status", "completed_at"])
        except Enrollment.DoesNotExist:
            pass


class LessonProgressViewSet(viewsets.ModelViewSet):
    """ViewSet for lesson progress tracking."""

    serializer_class = LessonProgressSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return LessonProgress.objects.filter(
            student=self.request.user
        ).select_related("lesson", "lesson__course")


class LessonNoteViewSet(viewsets.ModelViewSet):
    """ViewSet for lesson notes."""

    serializer_class = LessonNoteSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        lesson_id = self.kwargs.get("lesson_id")
        return LessonNote.objects.filter(
            student=self.request.user,
            lesson_id=lesson_id,
        ).order_by("-timestamp")

    def perform_create(self, serializer):
        lesson_id = self.kwargs.get("lesson_id")
        lesson = Lesson.objects.get(id=lesson_id)
        serializer.save(student=self.request.user, lesson=lesson)


class CourseContentView(generics.RetrieveAPIView):
    """Get complete course content with chapters and lessons."""

    permission_classes = [IsAuthenticated]
    serializer_class = LessonListSerializer

    def get(self, request, course_id):
        course = get_object_or_404(Course, id=course_id)
        
        # Check access
        if course.teacher != request.user and not request.user.is_admin:
            if not Enrollment.objects.filter(student=request.user, course=course).exists():
                if not course.allow_guest_access:
                    return Response({
                        "success": False,
                        "message": "You must be enrolled to access course content.",
                    }, status=status.HTTP_403_FORBIDDEN)
        
        chapters = Chapter.objects.filter(course=course).prefetch_related(
            "lessons"
        ).order_by("order")
        
        data = []
        for chapter in chapters:
            chapter_data = {
                "id": chapter.id,
                "title": chapter.title,
                "description": chapter.description,
                "order": chapter.order,
                "lessons": [],
            }
            
            for lesson in chapter.lessons.all():
                if lesson.status == Lesson.Status.PUBLISHED or course.teacher == request.user:
                    lesson_data = LessonListSerializer(lesson, context={"request": request}).data
                    chapter_data["lessons"].append(lesson_data)
            
            data.append(chapter_data)
        
        return Response({
            "success": True,
            "course": {
                "id": course.id,
                "title": course.title,
                "slug": course.slug,
            },
            "chapters": data,
        })
