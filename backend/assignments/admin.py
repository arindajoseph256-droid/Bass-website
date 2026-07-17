from django.contrib import admin
from .models import (
    Assignment, Submission, SubmissionComment,
    SubmissionAttachment, AssignmentGrade,
)


class SubmissionInline(admin.TabularInline):
    model = Submission
    extra = 0
    readonly_fields = ["student", "status", "score", "submitted_at"]
    can_delete = False


@admin.register(Assignment)
class AssignmentAdmin(admin.ModelAdmin):
    list_display = [
        "title", "course", "max_score", "passing_score",
        "due_date", "is_active", "submissions_count",
    ]
    list_filter = ["is_active", "due_date", "course"]
    search_fields = ["title", "course__title", "description"]
    raw_id_fields = ["course", "lesson"]
    date_hierarchy = "due_date"
    inlines = [SubmissionInline]

    def submissions_count(self, obj):
        return obj.submissions.count()
    submissions_count.short_description = "Submissions"


@admin.register(Submission)
class SubmissionAdmin(admin.ModelAdmin):
    list_display = [
        "assignment", "student", "status", "score",
        "is_passed", "late_submission", "submitted_at",
    ]
    list_filter = ["status", "is_passed", "late_submission", "submitted_at"]
    search_fields = ["assignment__title", "student__email"]
    raw_id_fields = ["assignment", "student", "graded_by"]
    date_hierarchy = "submitted_at"


@admin.register(SubmissionComment)
class SubmissionCommentAdmin(admin.ModelAdmin):
    list_display = ["submission", "user", "is_private", "created_at"]
    list_filter = ["is_private", "created_at"]
    search_fields = ["submission__assignment__title", "user__email", "content"]


@admin.register(SubmissionAttachment)
class SubmissionAttachmentAdmin(admin.ModelAdmin):
    list_display = ["submission", "filename", "file_size", "uploaded_at"]
    search_fields = ["submission__assignment__title", "filename"]
    raw_id_fields = ["submission"]


@admin.register(AssignmentGrade)
class AssignmentGradeAdmin(admin.ModelAdmin):
    list_display = ["submission", "criterion", "points_earned", "max_points"]
    search_fields = ["submission__assignment__title", "criterion"]
    raw_id_fields = ["submission"]
