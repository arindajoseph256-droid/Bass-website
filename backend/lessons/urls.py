from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    ChapterViewSet, LessonViewSet,
    LessonProgressViewSet, LessonNoteViewSet,
    CourseContentView,
)

router = DefaultRouter()
router.register("progress", LessonProgressViewSet, basename="lesson-progress")

urlpatterns = [
    path("courses/<int:course_id>/chapters/", ChapterViewSet.as_view({"get": "list", "post": "create"}), name="chapter-list"),
    path("courses/<int:course_id>/chapters/<int:pk>/", ChapterViewSet.as_view({"get": "retrieve", "put": "update", "delete": "destroy"}), name="chapter-detail"),
    path("courses/<int:course_id>/lessons/", LessonViewSet.as_view({"get": "list", "post": "create"}), name="lesson-list"),
    path("courses/<int:course_id>/lessons/<slug:slug>/", LessonViewSet.as_view({"get": "retrieve", "put": "update", "delete": "destroy"}), name="lesson-detail"),
    path("lessons/<int:lesson_id>/notes/", LessonNoteViewSet.as_view({"get": "list", "post": "create"}), name="lesson-notes"),
    path("courses/<int:course_id>/content/", CourseContentView.as_view(), name="course-content"),
    path("", include(router.urls)),
]
