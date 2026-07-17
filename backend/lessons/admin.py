from django.contrib import admin
from .models import Chapter, Lesson, LessonProgress, LessonResource, LessonNote


class LessonInline(admin.TabularInline):
    model = Lesson
    extra = 1
    fields = ["title", "type", "duration", "order", "is_free_preview", "status"]


@admin.register(Chapter)
class ChapterAdmin(admin.ModelAdmin):
    list_display = ["title", "course", "order", "total_lessons", "total_duration", "created_at"]
    list_filter = ["course", "created_at"]
    search_fields = ["title", "course__title"]
    raw_id_fields = ["course"]
    inlines = [LessonInline]


@admin.register(Lesson)
class LessonAdmin(admin.ModelAdmin):
    list_display = ["title", "course", "chapter", "type", "duration", "status", "is_free_preview", "order"]
    list_filter = ["type", "status", "is_free_preview", "course", "created_at"]
    search_fields = ["title", "course__title", "description"]
    raw_id_fields = ["course", "chapter"]
    prepopulated_fields = {"slug": ("title",)}
    date_hierarchy = "created_at"

    fieldsets = (
        ("Basic Info", {"fields": ("course", "chapter", "title", "slug", "description", "type", "order")}),
        ("Content", {"fields": ("content", "video_url", "video_file", "video_duration", "pdf_file", "thumbnail")}),
        ("Settings", {"fields": ("is_free_preview", "status", "duration", "live_url", "scheduled_at")}),
    )


@admin.register(LessonProgress)
class LessonProgressAdmin(admin.ModelAdmin):
    list_display = ["student", "lesson", "is_completed", "watched_duration", "last_position", "updated_at"]
    list_filter = ["is_completed", "updated_at"]
    search_fields = ["student__email", "lesson__title"]
    raw_id_fields = ["student", "lesson"]


@admin.register(LessonResource)
class LessonResourceAdmin(admin.ModelAdmin):
    list_display = ["title", "lesson", "type", "order", "created_at"]
    list_filter = ["type", "created_at"]
    search_fields = ["title", "lesson__title"]
    raw_id_fields = ["lesson"]


@admin.register(LessonNote)
class LessonNoteAdmin(admin.ModelAdmin):
    list_display = ["student", "lesson", "timestamp", "created_at"]
    list_filter = ["created_at"]
    search_fields = ["student__email", "lesson__title", "content"]
    raw_id_fields = ["student", "lesson"]
