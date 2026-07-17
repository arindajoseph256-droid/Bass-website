from django.contrib import admin
from .models import Forum, Topic, Post, Reply, Like, Report


@admin.register(Forum)
class ForumAdmin(admin.ModelAdmin):
    list_display = ["name", "course", "is_active", "order", "topics_count", "posts_count"]
    list_filter = ["is_active", "course"]
    search_fields = ["name", "description"]


@admin.register(Topic)
class TopicAdmin(admin.ModelAdmin):
    list_display = ["title", "forum", "author", "views", "is_pinned", "is_locked", "created_at"]
    list_filter = ["is_pinned", "is_locked", "forum", "created_at"]
    search_fields = ["title", "content", "author__email"]
    raw_id_fields = ["forum", "author"]


@admin.register(Post)
class PostAdmin(admin.ModelAdmin):
    list_display = ["topic", "author", "is_deleted", "created_at"]
    list_filter = ["is_deleted", "created_at"]
    search_fields = ["content", "author__email"]
    raw_id_fields = ["topic", "author"]


@admin.register(Reply)
class ReplyAdmin(admin.ModelAdmin):
    list_display = ["post", "author", "is_deleted", "created_at"]
    list_filter = ["is_deleted", "created_at"]
    search_fields = ["content", "author__email"]
    raw_id_fields = ["post", "author"]


@admin.register(Report)
class ReportAdmin(admin.ModelAdmin):
    list_display = ["reason", "reporter", "topic", "is_resolved", "created_at"]
    list_filter = ["reason", "is_resolved", "created_at"]
    search_fields = ["description", "reporter__email"]
    raw_id_fields = ["reporter", "topic", "post", "resolved_by"]
