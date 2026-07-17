from rest_framework import viewsets, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated, AllowAny
from django.shortcuts import get_object_or_404

from common.paginations import StandardResultsSetPagination
from common.permissions import IsModeratorUser
from .models import Forum, Topic, Post, Reply, Like, Report
from .serializers import (
    ForumSerializer, TopicSerializer, TopicDetailSerializer,
    PostSerializer, ReplySerializer, ReportSerializer,
)


class ForumViewSet(viewsets.ModelViewSet):
    """ViewSet for forums."""

    queryset = Forum.objects.filter(is_active=True)
    serializer_class = ForumSerializer
    permission_classes = [AllowAny]
    pagination_class = None

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsModeratorUser()]
        return super().get_permissions()


class TopicViewSet(viewsets.ModelViewSet):
    """ViewSet for forum topics."""

    serializer_class = TopicSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        forum_id = self.kwargs.get("forum_id")
        queryset = Topic.objects.filter(is_deleted=False)
        if forum_id:
            queryset = queryset.filter(forum_id=forum_id)
        return queryset.select_related("forum", "author")

    def get_serializer_class(self):
        if self.action == "retrieve":
            return TopicDetailSerializer
        return TopicSerializer

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        instance.views += 1
        instance.save(update_fields=["views"])
        serializer = self.get_serializer(instance)
        return Response({
            "success": True,
            "topic": serializer.data,
        })

    def perform_create(self, serializer):
        forum_id = self.kwargs.get("forum_id")
        forum = Forum.objects.get(id=forum_id)
        serializer.save(author=self.request.user, forum=forum)


class PostViewSet(viewsets.ModelViewSet):
    """ViewSet for forum posts."""

    serializer_class = PostSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        topic_id = self.kwargs.get("topic_id")
        return Post.objects.filter(
            topic_id=topic_id,
            is_deleted=False,
        ).select_related("author")

    def perform_create(self, serializer):
        topic_id = self.kwargs.get("topic_id")
        topic = Topic.objects.get(id=topic_id)
        serializer.save(author=self.request.user, topic=topic)

    @action(detail=True, methods=["post"])
    def like(self, request, topic_id=None, pk=None):
        post = self.get_object()
        like, created = Like.objects.get_or_create(user=request.user, post=post)
        if not created:
            like.delete()
            return Response({"success": True, "liked": False})
        return Response({"success": True, "liked": True})


class ReplyViewSet(viewsets.ModelViewSet):
    """ViewSet for replies."""

    serializer_class = ReplySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = None

    def get_queryset(self):
        post_id = self.kwargs.get("post_id")
        return Reply.objects.filter(
            post_id=post_id,
            is_deleted=False,
        ).select_related("author")

    def perform_create(self, serializer):
        post_id = self.kwargs.get("post_id")
        post = Post.objects.get(id=post_id)
        serializer.save(author=self.request.user, post=post)

    @action(detail=True, methods=["post"])
    def like(self, request, post_id=None, pk=None):
        reply = self.get_object()
        like, created = Like.objects.get_or_create(user=request.user, reply=reply)
        if not created:
            like.delete()
            return Response({"success": True, "liked": False})
        return Response({"success": True, "liked": True})


class ReportViewSet(viewsets.ModelViewSet):
    """ViewSet for reports."""

    serializer_class = ReportSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        if self.request.user.is_moderator or self.request.user.is_admin:
            return Report.objects.all()
        return Report.objects.filter(reporter=self.request.user)

    def perform_create(self, serializer):
        serializer.save(reporter=self.request.user)

    @action(detail=True, methods=["post"])
    def resolve(self, request, pk=None):
        report = self.get_object()
        report.is_resolved = True
        report.resolved_by = request.user
        report.save()
        return Response({"success": True, "message": "Report resolved."})
