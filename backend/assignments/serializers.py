from rest_framework import serializers
from django.contrib.auth import get_user_model
from django.utils import timezone
from .models import Assignment, Submission, SubmissionComment, SubmissionAttachment, AssignmentGrade

User = get_user_model()


class AssignmentListSerializer(serializers.ModelSerializer):
    """Serializer for assignment list view."""

    course_title = serializers.CharField(source="course.title", read_only=True)
    submissions_count = serializers.IntegerField()
    is_available = serializers.BooleanField()
    is_past_due = serializers.BooleanField()
    submissions_count = serializers.SerializerMethodField()

    class Meta:
        model = Assignment
        fields = [
            "id", "title", "course_title", "max_score", "passing_score",
            "due_date", "allow_late_submission", "is_active",
            "is_available", "is_past_due", "submissions_count",
        ]

    def get_submissions_count(self, obj):
        return obj.submissions.count()


class AssignmentDetailSerializer(serializers.ModelSerializer):
    """Serializer for assignment detail view."""

    course = serializers.SerializerMethodField()
    user_submission = serializers.SerializerMethodField()

    class Meta:
        model = Assignment
        fields = [
            "id", "title", "description", "instructions", "attachment",
            "max_score", "passing_score", "allow_late_submission",
            "late_penalty", "max_attempts", "available_from", "due_date",
            "allow_submission_until", "rubric", "course", "user_submission",
            "is_available", "is_past_due", "created_at", "updated_at",
        ]

    def get_course(self, obj):
        return {
            "id": obj.course.id,
            "title": obj.course.title,
            "slug": obj.course.slug,
        }

    def get_user_submission(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            submission = obj.submissions.filter(student=request.user).first()
            if submission:
                return SubmissionSerializer(submission).data
        return None


class AssignmentCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating assignments."""

    class Meta:
        model = Assignment
        fields = [
            "title", "description", "instructions", "attachment",
            "lesson", "max_score", "passing_score", "allow_late_submission",
            "late_penalty", "max_attempts", "is_active", "available_from",
            "due_date", "allow_submission_until", "rubric",
        ]


class SubmissionAttachmentSerializer(serializers.ModelSerializer):
    """Serializer for submission attachments."""

    class Meta:
        model = SubmissionAttachment
        fields = ["id", "file", "filename", "file_size", "mime_type", "uploaded_at"]


class SubmissionListSerializer(serializers.ModelSerializer):
    """Serializer for submission list view."""

    student_name = serializers.SerializerMethodField()
    is_graded = serializers.SerializerMethodField()

    class Meta:
        model = Submission
        fields = [
            "id", "assignment", "student_name", "status", "score",
            "percentage", "is_passed", "submitted_at", "is_graded",
        ]

    def get_student_name(self, obj):
        return obj.student.get_full_name()

    def get_is_graded(self, obj):
        return obj.status == Submission.Status.GRADED


class SubmissionDetailSerializer(serializers.ModelSerializer):
    """Serializer for submission detail view."""

    student = serializers.SerializerMethodField()
    assignment = serializers.SerializerMethodField()
    graded_by_name = serializers.SerializerMethodField()
    files = SubmissionAttachmentSerializer(many=True, read_only=True)
    comments = serializers.SerializerMethodField()

    class Meta:
        model = Submission
        fields = [
            "id", "assignment", "student", "content", "files",
            "status", "score", "percentage", "is_passed",
            "late_submission", "late_penalty_applied", "feedback",
            "graded_by_name", "submitted_at", "graded_at",
            "comments", "can_resubmit", "created_at", "updated_at",
        ]

    def get_student(self, obj):
        return {
            "id": obj.student.id,
            "name": obj.student.get_full_name(),
            "email": obj.student.email,
            "profile_image": obj.student.profile_image.url if obj.student.profile_image else None,
        }

    def get_assignment(self, obj):
        return {
            "id": obj.assignment.id,
            "title": obj.assignment.title,
            "max_score": obj.assignment.max_score,
            "passing_score": obj.assignment.passing_score,
        }

    def get_graded_by_name(self, obj):
        if obj.graded_by:
            return obj.graded_by.get_full_name()
        return None

    def get_comments(self, obj):
        request = self.context.get("request")
        comments = obj.comments.all()
        if request and not (request.user.is_teacher or request.user.is_admin):
            comments = comments.filter(is_private=False)
        return SubmissionCommentSerializer(comments, many=True).data


class SubmissionCreateSerializer(serializers.Serializer):
    """Serializer for creating submissions."""

    content = serializers.CharField(required=False, allow_blank=True)
    files = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
        write_only=True,
    )

    def validate(self, attrs):
        assignment = self.context.get("assignment")
        user = self.context.get("user")
        
        if not assignment.is_available:
            raise serializers.ValidationError("This assignment is not available.")

        existing = Submission.objects.filter(assignment=assignment, student=user).first()
        if existing and existing.status != Submission.Status.DRAFT:
            if existing.assignment.max_attempts <= 1:
                raise serializers.ValidationError("You have already submitted this assignment.")

        if assignment.is_past_due and not assignment.allow_late_submission:
            raise serializers.ValidationError("Late submissions are not allowed.")

        return attrs


class SubmissionGradeSerializer(serializers.Serializer):
    """Serializer for grading submissions."""

    score = serializers.IntegerField(min_value=0)
    feedback = serializers.CharField(required=False, allow_blank=True)
    status = serializers.ChoiceField(
        choices=[Submission.Status.GRADED, Submission.Status.RETURNED],
        default=Submission.Status.GRADED,
    )
    grade_breakdown = serializers.ListField(
        child=serializers.DictField(),
        required=False,
    )


class SubmissionCommentSerializer(serializers.ModelSerializer):
    """Serializer for submission comments."""

    user_name = serializers.SerializerMethodField()

    class Meta:
        model = SubmissionComment
        fields = ["id", "content", "user_name", "is_private", "created_at", "updated_at"]

    def get_user_name(self, obj):
        return obj.user.get_full_name()
