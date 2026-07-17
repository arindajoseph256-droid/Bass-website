from rest_framework import status
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.db.models import Q

from courses.models import Course
from accounts.models import User
from forums.models import Topic, Post


class GlobalSearchView:
    """Global search across all resources."""

    permission_classes = [IsAuthenticated]

    def get(self, request):
        query = request.query_params.get("q", "")
        search_type = request.query_params.get("type", "all")
        
        if not query:
            return Response({"results": {}})
        
        results = {}
        
        if search_type in ["all", "courses"]:
            results["courses"] = self._search_courses(query, request)
        
        if search_type in ["all", "users"]:
            results["users"] = self._search_users(query)
        
        if search_type in ["all", "forums"]:
            results["forums"] = self._search_forums(query)
        
        return Response({"query": query, "results": results})

    def _search_courses(self, query, request):
        courses = Course.objects.filter(
            Q(title__icontains=query) |
            Q(short_description__icontains=query) |
            Q(description__icontains=query),
            status=Course.Status.PUBLISHED
        ).select_related("teacher", "category")[:10]
        
        return [{
            "id": c.id,
            "title": c.title,
            "slug": c.slug,
            "teacher": c.teacher.get_full_name(),
            "category": c.category.name if c.category else None,
            "thumbnail": c.thumbnail.url if c.thumbnail else None,
            "total_students": c.total_students,
            "total_rating": float(c.total_rating),
        } for c in courses]

    def _search_users(self, query):
        users = User.objects.filter(
            Q(email__icontains=query) |
            Q(first_name__icontains=query) |
            Q(last_name__icontains=query) |
            Q(username__icontains=query),
            is_active=True
        )[:10]
        
        return [{
            "id": u.id,
            "name": u.get_full_name(),
            "email": u.email,
            "role": u.role,
            "profile_image": u.profile_image.url if u.profile_image else None,
        } for u in users]

    def _search_forums(self, query):
        topics = Topic.objects.filter(
            Q(title__icontains=query) |
            Q(content__icontains=query),
            is_deleted=False
        ).select_related("forum", "author")[:10]
        
        return [{
            "id": t.id,
            "title": t.title,
            "forum": t.forum.name,
            "author": t.author.get_full_name(),
            "views": t.views,
            "replies": t.replies_count,
        } for t in topics]
