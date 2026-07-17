from django.contrib import admin
from .models import Quiz, Question, Answer, QuizAttempt, StudentAnswer, QuizResult


class AnswerInline(admin.TabularInline):
    model = Answer
    extra = 2


class QuestionInline(admin.TabularInline):
    model = Question
    extra = 1


@admin.register(Quiz)
class QuizAdmin(admin.ModelAdmin):
    list_display = [
        "title", "course", "total_questions", "time_limit",
        "max_attempts", "passing_score", "is_active",
        "total_attempts", "average_score",
    ]
    list_filter = ["is_active", "course", "created_at"]
    search_fields = ["title", "course__title", "description"]
    raw_id_fields = ["course", "lesson"]
    date_hierarchy = "created_at"
    inlines = [QuestionInline]

    def total_questions(self, obj):
        return obj.questions.count()
    total_questions.short_description = "Questions"


@admin.register(Question)
class QuestionAdmin(admin.ModelAdmin):
    list_display = ["quiz", "type", "question", "points", "order", "created_at"]
    list_filter = ["type", "quiz", "created_at"]
    search_fields = ["question", "quiz__title"]
    raw_id_fields = ["quiz"]
    inlines = [AnswerInline]


@admin.register(Answer)
class AnswerAdmin(admin.ModelAdmin):
    list_display = ["question", "answer", "is_correct", "order"]
    list_filter = ["is_correct", "question__quiz"]
    search_fields = ["answer", "question__question"]


@admin.register(QuizAttempt)
class QuizAttemptAdmin(admin.ModelAdmin):
    list_display = [
        "quiz", "student", "status", "score", "percentage",
        "is_passed", "attempt_number", "started_at", "completed_at",
    ]
    list_filter = ["status", "is_passed", "started_at"]
    search_fields = ["quiz__title", "student__email"]
    raw_id_fields = ["quiz", "student"]
    date_hierarchy = "started_at"


@admin.register(StudentAnswer)
class StudentAnswerAdmin(admin.ModelAdmin):
    list_display = ["attempt", "question", "is_correct", "points_earned", "created_at"]
    list_filter = ["is_correct", "created_at"]
    search_fields = ["attempt__student__email", "question__question"]


@admin.register(QuizResult)
class QuizResultAdmin(admin.ModelAdmin):
    list_display = [
        "attempt", "correct_answers", "wrong_answers",
        "skipped_questions", "time_spent", "created_at",
    ]
    search_fields = ["attempt__quiz__title", "attempt__student__email"]
