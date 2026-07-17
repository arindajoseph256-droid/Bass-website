from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone

User = get_user_model()


class Forum(models.Model):
    """Forum category model."""

    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="forums",
    )
    name = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    is_active = models.BooleanField(default=True)
    order = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["order", "name"]

    def __str__(self):
        return self.name

    @property
    def topics_count(self):
        return self.topics.count()

    @property
    def posts_count(self):
        return Post.objects.filter(topic__forum=self).count()


class Topic(models.Model):
    """Forum topic model."""

    forum = models.ForeignKey(
        Forum,
        on_delete=models.CASCADE,
        related_name="topics",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="forum_topics",
    )
    title = models.CharField(max_length=255)
    content = models.TextField()
    is_pinned = models.BooleanField(default=False)
    is_locked = models.BooleanField(default=False)
    is_deleted = models.BooleanField(default=False)
    views = models.IntegerField(default=0)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-is_pinned", "-created_at"]
        indexes = [models.Index(fields=["forum", "-created_at"])]

    def __str__(self):
        return self.title

    @property
    def replies_count(self):
        return self.posts.count()

    @property
    def last_post(self):
        return self.posts.order_by("-created_at").first()


class Post(models.Model):
    """Forum post model."""

    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        related_name="posts",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="forum_posts",
    )
    content = models.TextField()
    is_deleted = models.BooleanField(default=False)
    edited_at = models.DateTimeField(null=True, blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]
        indexes = [models.Index(fields=["topic", "created_at"])]

    def __str__(self):
        return f"{self.author} on {self.topic.title}"


class Reply(models.Model):
    """Reply to a post."""

    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        related_name="replies",
    )
    author = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="forum_replies",
    )
    content = models.TextField()
    is_deleted = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["created_at"]

    def __str__(self):
        return f"{self.author} replying to {self.post.author}"


class Like(models.Model):
    """Likes for posts and replies."""

    user = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="forum_likes",
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="likes",
    )
    reply = models.ForeignKey(
        Reply,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="likes",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        unique_together = ["user", "post", "reply"]

    def __str__(self):
        target = self.post or self.reply
        return f"{self.user} liked {target}"


class Report(models.Model):
    """Report abuse model."""

    class Reason(models.TextChoices):
        SPAM = "spam", "Spam"
        HARASSMENT = "harassment", "Harassment"
        INAPPROPRIATE = "inappropriate", "Inappropriate Content"
        OTHER = "other", "Other"

    reporter = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="forum_reports",
    )
    topic = models.ForeignKey(
        Topic,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="reports",
    )
    post = models.ForeignKey(
        Post,
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="reports",
    )
    reason = models.CharField(max_length=20, choices=Reason.choices)
    description = models.TextField(blank=True)
    is_resolved = models.BooleanField(default=False)
    resolved_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="resolved_reports",
    )
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return f"Report: {self.reason}"
