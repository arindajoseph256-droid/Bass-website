from rest_framework import viewsets, generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
from django.utils import timezone

from courses.models import Course, Enrollment
from common.permissions import IsTeacherOrAdmin, IsStudentUser
from common.paginations import StandardResultsSetPagination
from .models import Assignment, Submission, SubmissionComment, AssignmentGrade
from .serializers import (
    AssignmentListSerializer, AssignmentDetailSerializer,
    AssignmentCreateUpdateSerializer, SubmissionListSerializer,
    SubmissionDetailSerializer, SubmissionCreateSerializer,
    SubmissionGradeSerializer, SubmissionCommentSerializer,
)


class AssignmentViewSet(viewsets.ModelViewSet):
    """ViewSet for assignments."""

    queryset = Assignment.objects.all()
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        if self.action == "list":
            return AssignmentListSerializer
        if self.action == "retrieve":
            return AssignmentDetailSerializer
        return AssignmentCreateUpdateSerializer

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
        
        return queryset.select_related("course", "lesson")

    def perform_create(self, serializer):
        course_id = self.request.data.get("course")
        course = Course.objects.get(id=course_id)
        
        if course.teacher != self.request.user and not self.request.user.is_admin:
            raise PermissionError("You don't have permission to create assignments for this course.")
        
        serializer.save(course=course)

    @action(detail=True, methods=["get"])
    def submissions(self, request, pk=None):
        """Get all submissions for an assignment."""
        assignment = self.get_object()
        submissions = assignment.submissions.all()
        page = self.paginate_queryset(submissions)
        if page is not None:
            serializer = SubmissionListSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = SubmissionListSerializer(submissions, many=True)
        return Response({
            "success": True,
            "submissions": serializer.data,
        })


class SubmissionViewSet(viewsets.ModelViewSet):
    """ViewSet for submissions."""

    serializer_class = SubmissionListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_serializer_class(self):
        if self.action == "retrieve":
            return SubmissionDetailSerializer
        if self.action == "create":
            return SubmissionCreateSerializer
        return SubmissionListSerializer

    def get_queryset(self):
        if self.request.user.is_teacher or self.request.user.is_admin:
            assignment_id = self.kwargs.get("assignment_id")
            if assignment_id:
                return Submission.objects.filter(assignment_id=assignment_id)
            return Submission.objects.none()
        return Submission.objects.filter(student=self.request.user)

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance, context={"request": request})
        return Response({
            "success": True,
            "submission": serializer.data,
        })

    def create(self, request, *args, **kwargs):
        assignment_id = kwargs.get("assignment_id")
        assignment = get_object_or_404(Assignment, id=assignment_id)
        
        serializer = SubmissionCreateSerializer(
            data=request.data,
            context={"assignment": assignment, "user": request.user},
        )
        serializer.is_valid(raise_exception=True)
        
        submission, created = Submission.objects.get_or_create(
            assignment=assignment,
            student=request.user,
            defaults={
                "content": serializer.validated_data.get("content", ""),
                "status": Submission.Status.SUBMITTED,
                "submitted_at": timezone.now(),
            },
        )
        
        if not created:
            submission.content = serializer.validated_data.get("content", "")
            submission.status = Submission.Status.SUBMITTED
            submission.submitted_at = timezone.now()
            submission.save()
        
        # Check for late submission
        if assignment.is_past_due:
            submission.late_submission = True
            submission.save(update_fields=["late_submission"])
        
        # Add files if provided
        file_ids = serializer.validated_data.get("files", [])
        if file_ids:
            from uploads.models import UploadedFile
            files = UploadedFile.objects.filter(id__in=file_ids, uploaded_by=request.user)
            submission.attachments.set(files)
        
        return Response({
            "success": True,
            "message": "Submission saved successfully.",
            "submission": SubmissionDetailSerializer(submission, context={"request": request}).data,
        }, status=status.HTTP_201_CREATED if created else status.HTTP_200_OK)

    @action(detail=True, methods=["post"])
    def grade(self, request, pk=None, assignment_id=None):
        """Grade a submission."""
        submission = self.get_object()
        
        if submission.assignment.course.teacher != request.user and not request.user.is_admin:
            return Response({
                "success": False,
                "message": "You don't have permission to grade this submission.",
            }, status=status.HTTP_403_FORBIDDEN)
        
        serializer = SubmissionGradeSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        submission.score = serializer.validated_data["score"]
        submission.percentage = (submission.score / submission.assignment.max_score) * 100
        submission.feedback = serializer.validated_data.get("feedback", "")
        submission.status = serializer.validated_data["status"]
        submission.graded_by = request.user
        submission.graded_at = timezone.now()
        submission.is_passed = submission.score >= submission.assignment.passing_score
        
        # Apply late penalty
        if submission.late_submission:
            submission.score = submission.calculate_score()
        
        submission.save()
        
        # Save grade breakdown if provided
        breakdown = serializer.validated_data.get("grade_breakdown", [])
        for item in breakdown:
            AssignmentGrade.objects.update_or_create(
                submission=submission,
                criterion=item.get("criterion"),
                defaults={
                    "description": item.get("description", ""),
                    "max_points": item.get("max_points", 0),
                    "points_earned": item.get("points_earned", 0),
                    "feedback": item.get("feedback", ""),
                },
            )
        
        return Response({
            "success": True,
            "message": "Submission graded successfully.",
            "submission": SubmissionDetailSerializer(submission, context={"request": request}).data,
        })

    @action(detail=True, methods=["post"])
    def submit(self, request, pk=None, assignment_id=None):
        """Submit a draft submission."""
        submission = self.get_object()
        
        if submission.student != request.user:
            return Response({
                "success": False,
                "message": "You don't have permission to submit this.",
            }, status=status.HTTP_403_FORBIDDEN)
        
        if submission.status != Submission.Status.DRAFT:
            return Response({
                "success": False,
                "message": "This submission is already submitted.",
            }, status=status.HTTP_400_BAD_REQUEST)
        
        submission.status = Submission.Status.SUBMITTED
        submission.submitted_at = timezone.now()
        
        if submission.assignment.is_past_due:
            submission.late_submission = True
        
        submission.save()
        
        return Response({
            "success": True,
            "message": "Submission submitted successfully.",
        })


class SubmissionCommentViewSet(viewsets.ModelViewSet):
    """ViewSet for submission comments."""

    serializer_class = SubmissionCommentSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        submission_id = self.kwargs.get("submission_id")
        submission = get_object_or_404(Submission, id=submission_id)
        
        # Only allow grader or admin to view private comments
        if submission.graded_by == self.request.user or self.request.user.is_admin:
            return SubmissionComment.objects.filter(submission=submission)
        return SubmissionComment.objects.filter(submission=submission, is_private=False)

    def perform_create(self, serializer):
        submission_id = self.kwargs.get("submission_id")
        submission = get_object_or_404(Submission, id=submission_id)
        serializer.save(user=self.request.user, submission=submission)


class StudentAssignmentListView(generics.ListAPIView):
    """List assignments for a student."""

    serializer_class = AssignmentListSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        user = self.request.user
        course_id = self.kwargs.get("course_id")
        
        # Get courses user is enrolled in
        enrolled_course_ids = Enrollment.objects.filter(
            student=user
        ).values_list("course_id", flat=True)
        
        queryset = Assignment.objects.filter(
            course_id__in=enrolled_course_ids,
            is_active=True,
        )
        
        if course_id:
            queryset = queryset.filter(course_id=course_id)
        
        return queryset.select_related("course")
