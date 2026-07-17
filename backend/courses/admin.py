from django.contrib import admin
from .models import (
    Category, Tag, Course, CourseReview,
    Enrollment, Wishlist, Bookmark,
)


@admin.register(Category)
class CategoryAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "parent", "is_active", "order", "course_count"]
    list_filter = ["is_active", "parent"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}
    ordering = ["order", "name"]

    def course_count(self, obj):
        return obj.courses.filter(status=Course.Status.PUBLISHED).count()
    course_count.short_description = "Courses"


@admin.register(Tag)
class TagAdmin(admin.ModelAdmin):
    list_display = ["name", "slug", "created_at"]
    search_fields = ["name", "slug"]
    prepopulated_fields = {"slug": ("name",)}


@admin.register(Course)
class CourseAdmin(admin.ModelAdmin):
    list_display = [
        "title", "teacher", "category", "level", "status",
        "is_free", "price", "total_students", "total_rating",
        "is_featured", "is_popular", "published_at",
    ]
    list_filter = ["status", "level", "is_free", "is_featured", "is_popular", "category"]
    search_fields = ["title", "teacher__email", "short_description"]
    prepopulated_fields = {"slug": ("title",)}
    raw_id_fields = ["teacher", "category", "school"]
    date_hierarchy = "published_at"
    ordering = ["-created_at"]

    fieldsets = (
        ("Basic Info", {"fields": ("title", "slug", "short_description", "description")}),
        ("Media", {"fields": ("thumbnail", "preview_video")}),
        ("Pricing", {"fields": ("price", "discount_price", "is_free")}),
        ("Organization", {"fields": ("teacher", "school", "category", "tags")}),
        ("Content", {"fields": ("level", "language", "requirements", "outcomes")}),
        ("Settings", {"fields": ("status", "is_featured", "is_popular", "allow_guest_access", "certificate_available", "max_students")}),
    )


@admin.register(CourseReview)
class CourseReviewAdmin(admin.ModelAdmin):
    list_display = ["course", "user", "rating", "is_approved", "created_at"]
    list_filter = ["is_approved", "rating", "created_at"]
    search_fields = ["course__title", "user__email", "comment"]
    raw_id_fields = ["course", "user"]


@admin.register(Enrollment)
class EnrollmentAdmin(admin.ModelAdmin):
    list_display = ["student", "course", "status", "progress", "enrolled_at", "completed_at"]
    list_filter = ["status", "enrolled_at", "completed_at"]
    search_fields = ["student__email", "course__title"]
    raw_id_fields = ["student", "course"]
    date_hierarchy = "enrolled_at"


@admin.register(Wishlist)
class WishlistAdmin(admin.ModelAdmin):
    list_display = ["student", "course", "added_at"]
    search_fields = ["student__email", "course__title"]
    raw_id_fields = ["student", "course"]


@admin.register(Bookmark)
class BookmarkAdmin(admin.ModelAdmin):
    list_display = ["student", "course", "lesson", "created_at"]
    search_fields = ["student__email", "course__title", "lesson__title"]
    raw_id_fields = ["student", "course", "lesson"]
