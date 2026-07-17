from rest_framework import viewsets, generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone
from django.db.models import Avg

from courses.models import Course, Enrollment
from common.permissions import IsTeacherOrAdmin, IsStudentUser
from common.paginations import StandardResultsSetPagination
from .models import Quiz, Question, Answer, QuizAttempt, StudentAnswer, QuizResult
from .serializers import (
    QuizListSerializer, QuizDetailSerializer, QuizTakingSerializer,
    QuizCreateUpdateSerializer, QuestionSerializer, QuestionWithAnswersSerializer,
    QuestionCreateUpdateSerializer, AnswerSerializer, AnswerCreateUpdateSerializer,
    QuizAttemptSerializer, QuizAttemptDetailSerializer, QuizSubmissionSerializer,
)


class QuizViewSet(viewsets.ModelViewSet):
    """ViewSet for quizzes."""

    queryset = Quiz.objects.all()
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        if self.action == "list":
            return QuizListSerializer
        if self.action == "retrieve":
            return QuizDetailSerializer
        if self.action in ["create", "update", "partial_update"]:
            return QuizCreateUpdateSerializer
        if self.action == "take":
            return QuizTakingSerializer
        return QuizDetailSerializer

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsTeacherOrAdmin()]
        return super().get_permissions()

    def get_queryset(self):
        queryset = super().get_queryset()
        
        course_id = self.request.query_params.get("course")
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        
        if self.action == "list":
            if not (self.request.user.is_teacher or self.request.user.is_admin):
                queryset = queryset.filter(is_active=True)
        
        return queryset.prefetch_related("questions")

    @action(detail=True, methods=["post"])
    def take(self, request, pk=None):
        """Start or resume a quiz attempt."""
        quiz = self.get_object()
        
        if not quiz.is_available:
            return Response({
                "success": False,
                "message": "This quiz is not available.",
            }, status=status.HTTP_403_FORBIDDEN)
        
        # Check enrollment
        if quiz.course.teacher != request.user and not request.user.is_admin:
            if not Enrollment.objects.filter(student=request.user, course=quiz.course).exists():
                return Response({
                    "success": False,
                    "message": "You must be enrolled to take this quiz.",
                }, status=status.HTTP_403_FORBIDDEN)
        
        # Check for existing attempt
        attempt = quiz.attempts.filter(
            student=request.user,
            status__in=[QuizAttempt.Status.IN_PROGRESS, QuizAttempt.Status.COMPLETED],
        ).order_by("-attempt_number").first()
        
        if attempt and attempt.status == QuizAttempt.Status.COMPLETED:
            if not attempt.can_retake:
                return Response({
                    "success": False,
                    "message": "You have reached the maximum number of attempts.",
                }, status=status.HTTP_400_BAD_REQUEST)
            
            # Create new attempt
            attempt = QuizAttempt.objects.create(
                quiz=quiz,
                student=request.user,
                attempt_number=attempt.attempt_number + 1,
            )
        elif not attempt:
            attempt = QuizAttempt.objects.create(
                quiz=quiz,
                student=request.user,
                attempt_number=1,
                ip_address=self.get_client_ip(request),
                user_agent=request.META.get("HTTP_USER_AGENT", "")[:500],
            )
        
        serializer = QuizTakingSerializer(quiz, context={"request": request})
        return Response({
            "success": True,
            "attempt_id": attempt.id,
            "attempt_number": attempt.attempt_number,
            "started_at": attempt.started_at,
            "quiz": serializer.data,
        })

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None):
        """Submit quiz answers."""
        quiz = self.get_object()
        
        attempt_id = request.data.get("attempt_id")
        if not attempt_id:
            return Response({
                "success": False,
                "message": "Attempt ID is required.",
            }, status=status.HTTP_400_BAD_REQUEST)
        
        attempt = get_object_or_404(QuizAttempt, id=attempt_id, quiz=quiz, student=request.user)
        
        if attempt.status != QuizAttempt.Status.IN_PROGRESS:
            return Response({
                "success": False,
                "message": "This attempt has already been submitted.",
            }, status=status.HTTP_400_BAD_REQUEST)
        
        serializer = QuizSubmissionSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        total_score = 0
        total_possible = 0
        correct_count = 0
        wrong_count = 0
        skipped = 0
        
        for answer_data in serializer.validated_data["answers"]:
            question = get_object_or_404(Question, id=answer_data["question_id"], quiz=quiz)
            total_possible += question.points
            
            student_answer, created = StudentAnswer.objects.get_or_create(
                attempt=attempt,
                question=question,
            )
            
            if answer_data.get("selected_answers"):
                selected = Answer.objects.filter(id__in=answer_data["selected_answers"])
                student_answer.selected_answers.set(selected)
            
            if answer_data.get("text_answer"):
                student_answer.text_answer = answer_data["text_answer"]
            
            student_answer.grade_answer()
            total_score += student_answer.points_earned
            
            if student_answer.points_earned == question.points:
                correct_count += 1
            elif student_answer.points_earned > 0:
                wrong_count += 1
            elif not answer_data.get("selected_answers") and not answer_data.get("text_answer"):
                skipped += 1
            else:
                wrong_count += 1
            
            student_answer.save()
        
        # Update attempt
        attempt.score = total_score
        attempt.percentage = (total_score / total_possible * 100) if total_possible > 0 else 0
        attempt.is_passed = attempt.percentage >= quiz.passing_score
        attempt.status = QuizAttempt.Status.COMPLETED
        attempt.completed_at = timezone.now()
        attempt.time_taken = serializer.validated_data.get("time_spent", 0)
        attempt.save()
        
        # Update quiz stats
        quiz.total_attempts += 1
        avg_score = quiz.attempts.filter(status=QuizAttempt.Status.COMPLETED).aggregate(Avg("percentage"))
        quiz.average_score = avg_score["percentage__avg"] or 0
        quiz.save(update_fields=["total_attempts", "average_score"])
        
        # Create result
        QuizResult.objects.update_or_create(
            attempt=attempt,
            defaults={
                "correct_answers": correct_count,
                "wrong_answers": wrong_count,
                "skipped_questions": skipped,
                "time_spent": attempt.time_taken,
            },
        )
        
        return Response({
            "success": True,
            "message": "Quiz submitted successfully.",
            "result": {
                "score": attempt.score,
                "percentage": float(attempt.percentage),
                "is_passed": attempt.is_passed,
                "correct_answers": correct_count,
                "wrong_answers": wrong_count,
                "skipped_questions": skipped,
                "show_answers": quiz.show_correct_answers,
            },
            "attempt": QuizAttemptSerializer(attempt).data,
        })

    def get_client_ip(self, request):
        x_forwarded_for = request.META.get("HTTP_X_FORWARDED_FOR")
        if x_forwarded_for:
            return x_forwarded_for.split(",")[0]
        return request.META.get("REMOTE_ADDR")


class QuestionViewSet(viewsets.ModelViewSet):
    """ViewSet for questions."""

    serializer_class = QuestionSerializer
    permission_classes = [IsTeacherOrAdmin]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        quiz_id = self.kwargs.get("quiz_id")
        return Question.objects.filter(quiz_id=quiz_id)

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return QuestionCreateUpdateSerializer
        return QuestionWithAnswersSerializer

    def perform_create(self, serializer):
        quiz_id = self.kwargs.get("quiz_id")
        quiz = Quiz.objects.get(id=quiz_id)
        serializer.save(quiz=quiz)


class AnswerViewSet(viewsets.ModelViewSet):
    """ViewSet for answers."""

    serializer_class = AnswerSerializer
    permission_classes = [IsTeacherOrAdmin]
    pagination_class = None

    def get_queryset(self):
        question_id = self.kwargs.get("question_id")
        return Answer.objects.filter(question_id=question_id)

    def get_serializer_class(self):
        if self.action in ["create", "update", "partial_update"]:
            return AnswerCreateUpdateSerializer
        return AnswerSerializer

    def perform_create(self, serializer):
        question_id = self.kwargs.get("question_id")
        question = Question.objects.get(id=question_id)
        serializer.save(question=question)


class QuizAttemptViewSet(viewsets.ModelViewSet):
    """ViewSet for quiz attempts."""

    serializer_class = QuizAttemptSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        if self.request.user.is_teacher or self.request.user.is_admin:
            quiz_id = self.kwargs.get("quiz_id")
            if quiz_id:
                return QuizAttempt.objects.filter(quiz_id=quiz_id)
            return QuizAttempt.objects.none()
        return QuizAttempt.objects.filter(student=self.request.user)

    def get_serializer_class(self):
        if self.action == "retrieve":
            return QuizAttemptDetailSerializer
        return QuizAttemptSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        show_answers = instance.quiz.show_correct_answers
        serializer = self.get_serializer(instance, context={"show_answers": show_answers})
        return Response({
            "success": True,
            "attempt": serializer.data,
        })


class StudentQuizListView(generics.ListAPIView):
    """List quizzes for a student."""

    serializer_class = QuizListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        course_id = self.kwargs.get("course_id")
        
        enrolled_course_ids = Enrollment.objects.filter(
            student=user
        ).values_list("course_id", flat=True)
        
        queryset = Quiz.objects.filter(
            course_id__in=enrolled_course_ids,
            is_active=True,
        )
        
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        
        return queryset
