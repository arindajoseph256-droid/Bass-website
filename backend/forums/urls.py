from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ForumViewSet, TopicViewSet, PostViewSet, ReplyViewSet, ReportViewSet

router = DefaultRouter()
router.register("reports", ReportViewSet, basename="report")

urlpatterns = [
    path("", ForumViewSet.as_view({"get": "list", "post": "create"}), name="forum-list"),
    path("<int:pk>/", ForumViewSet.as_view({"get": "retrieve", "put": "update", "delete": "destroy"}), name="forum-detail"),
    path("<int:forum_id>/topics/", TopicViewSet.as_view({"get": "list", "post": "create"}), name="topic-list"),
    path("<int:forum_id>/topics/<int:pk>/", TopicViewSet.as_view({"get": "retrieve", "put": "update", "delete": "destroy"}), name="topic-detail"),
    path("topics/<int:topic_id>/posts/", PostViewSet.as_view({"get": "list", "post": "create"}), name="post-list"),
    path("topics/<int:topic_id>/posts/<int:pk>/", PostViewSet.as_view({"get": "retrieve", "put": "update", "delete": "destroy"}), name="post-detail"),
    path("posts/<int:post_id>/replies/", ReplyViewSet.as_view({"get": "list", "post": "create"}), name="reply-list"),
    path("posts/<int:post_id>/replies/<int:pk>/", ReplyViewSet.as_view({"get": "retrieve", "put": "update", "delete": "destroy"}), name="reply-detail"),
    path("", include(router.urls)),
]
