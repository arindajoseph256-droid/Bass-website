from rest_framework import serializers
from .models import Forum, Topic, Post, Reply, Like, Report


class ForumSerializer(serializers.ModelSerializer):
    """Serializer for forums."""

    topics_count = serializers.IntegerField(read_only=True)
    posts_count = serializers.IntegerField(read_only=True)

    class Meta:
        model = Forum
        fields = ["id", "name", "description", "topics_count", "posts_count", "order"]


class TopicListSerializer(serializers.ModelSerializer):
    """Serializer for topic list."""

    author_name = serializers.SerializerMethodField()
    replies_count = serializers.IntegerField()
    last_post_info = serializers.SerializerMethodField()

    class Meta:
        model = Topic
        fields = [
            "id", "title", "author_name", "replies_count",
            "views", "is_pinned", "created_at", "last_post_info",
        ]

    def get_author_name(self, obj):
        return obj.author.get_full_name()

    def get_last_post_info(self, obj):
        last_post = obj.last_post
        if last_post:
            return {
                "author": last_post.author.get_full_name(),
                "created_at": last_post.created_at,
            }
        return None


class TopicDetailSerializer(serializers.ModelSerializer):
    """Serializer for topic detail with posts."""

    author = serializers.SerializerMethodField()
    posts = serializers.SerializerMethodField()

    class Meta:
        model = Topic
        fields = [
            "id", "title", "content", "author", "forum",
            "is_pinned", "is_locked", "views", "created_at",
            "updated_at", "posts",
        ]

    def get_author(self, obj):
        return {
            "id": obj.author.id,
            "name": obj.author.get_full_name(),
            "profile_image": obj.author.profile_image.url if obj.author.profile_image else None,
        }

    def get_posts(self, obj):
        posts = obj.posts.filter(is_deleted=False)
        return PostSerializer(posts, many=True).data


class PostSerializer(serializers.ModelSerializer):
    """Serializer for posts."""

    author = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()
    is_liked = serializers.SerializerMethodField()

    class Meta:
        model = Post
        fields = [
            "id", "content", "author", "likes_count", "is_liked",
            "edited_at", "created_at",
        ]

    def get_author(self, obj):
        return {
            "id": obj.author.id,
            "name": obj.author.get_full_name(),
            "profile_image": obj.author.profile_image.url if obj.author.profile_image else None,
        }

    def get_likes_count(self, obj):
        return obj.likes.count()

    def get_is_liked(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            return obj.likes.filter(user=request.user).exists()
        return False


class ReplySerializer(serializers.ModelSerializer):
    """Serializer for replies."""

    author = serializers.SerializerMethodField()
    likes_count = serializers.SerializerMethodField()

    class Meta:
        model = Reply
        fields = [
            "id", "content", "author", "likes_count",
            "created_at",
        ]

    def get_author(self, obj):
        return {
            "id": obj.author.id,
            "name": obj.author.get_full_name(),
            "profile_image": obj.author.profile_image.url if obj.author.profile_image else None,
        }

    def get_likes_count(self, obj):
        return obj.likes.count()


class ReportSerializer(serializers.ModelSerializer):
    """Serializer for reports."""

    reporter_name = serializers.SerializerMethodField()
    resolved_by_name = serializers.SerializerMethodField()

    class Meta:
        model = Report
        fields = [
            "id", "topic", "post", "reason", "description",
            "is_resolved", "reporter_name", "resolved_by_name",
            "created_at",
        ]

    def get_reporter_name(self, obj):
        return obj.reporter.get_full_name()

    def get_resolved_by_name(self, obj):
        if obj.resolved_by:
            return obj.resolved_by.get_full_name()
        return None
