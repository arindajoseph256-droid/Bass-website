from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    AssignmentViewSet, SubmissionViewSet,
    SubmissionCommentViewSet, StudentAssignmentListView,
)

router = DefaultRouter()
router.register("assignments", AssignmentViewSet, basename="assignment")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "assignments/<int:assignment_id>/submissions/",
        SubmissionViewSet.as_view({"get": "list", "post": "create"}),
        name="submission-list",
    ),
    path(
        "assignments/<int:assignment_id>/submissions/<int:pk>/",
        SubmissionViewSet.as_view({"get": "retrieve", "put": "update", "delete": "destroy"}),
        name="submission-detail",
    ),
    path(
        "assignments/<int:assignment_id>/submissions/<int:pk>/grade/",
        SubmissionViewSet.as_view({"post": "grade"}),
        name="submission-grade",
    ),
    path(
        "submissions/<int:submission_id>/comments/",
        SubmissionCommentViewSet.as_view({"get": "list", "post": "create"}),
        name="submission-comments",
    ),
    path(
        "courses/<int:course_id>/student-assignments/",
        StudentAssignmentListView.as_view(),
        name="student-assignments",
    ),
]
