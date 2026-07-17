from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    QuizViewSet, QuestionViewSet, AnswerViewSet,
    QuizAttemptViewSet, StudentQuizListView,
)

router = DefaultRouter()
router.register("quizzes", QuizViewSet, basename="quiz")

urlpatterns = [
    path("", include(router.urls)),
    path(
        "quizzes/<int:quiz_id>/questions/",
        QuestionViewSet.as_view({"get": "list", "post": "create"}),
        name="question-list",
    ),
    path(
        "quizzes/<int:quiz_id>/questions/<int:pk>/",
        QuestionViewSet.as_view({"get": "retrieve", "put": "update", "delete": "destroy"}),
        name="question-detail",
    ),
    path(
        "quizzes/<int:quiz_id>/questions/<int:question_id>/answers/",
        AnswerViewSet.as_view({"get": "list", "post": "create"}),
        name="answer-list",
    ),
    path(
        "quizzes/<int:quiz_id>/questions/<int:question_id>/answers/<int:pk>/",
        AnswerViewSet.as_view({"get": "retrieve", "put": "update", "delete": "destroy"}),
        name="answer-detail",
    ),
    path(
        "quizzes/<int:quiz_id>/attempts/",
        QuizAttemptViewSet.as_view({"get": "list"}),
        name="quiz-attempts",
    ),
    path(
        "quizzes/<int:quiz_id>/attempts/<int:pk>/",
        QuizAttemptViewSet.as_view({"get": "retrieve"}),
        name="quiz-attempt-detail",
    ),
    path(
        "courses/<int:course_id>/student-quizzes/",
        StudentQuizListView.as_view(),
        name="student-quizzes",
    ),
]
