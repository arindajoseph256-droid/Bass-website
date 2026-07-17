from rest_framework import viewsets, generics, status, serializers
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import AllowAny, IsAuthenticated
from django_filters.rest_framework import DjangoFilterBackend
from django.db.models import Q, Avg, Count
from django.utils import timezone

from common.paginations import StandardResultsSetPagination
from common.permissions import IsTeacherOrAdmin, IsStudentUser
from lessons.models import Lesson
from .models import (
    Category, Tag, Course, CourseReview,
    Enrollment, Wishlist, Bookmark,
)
from .serializers import (
    CategorySerializer, TagSerializer,
    CourseListSerializer, CourseDetailSerializer,
    CourseCreateUpdateSerializer, CourseReviewSerializer,
    EnrollmentSerializer, EnrollmentCreateSerializer,
    WishlistSerializer, BookmarkSerializer,
)


class CategoryViewSet(viewsets.ModelViewSet):
    """ViewSet for course categories."""

    queryset = Category.objects.filter(is_active=True)
    serializer_class = CategorySerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"
    pagination_class = None

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsTeacherOrAdmin()]
        return super().get_permissions()


class TagViewSet(viewsets.ModelViewSet):
    """ViewSet for course tags."""

    queryset = Tag.objects.all()
    serializer_class = TagSerializer
    permission_classes = [AllowAny]
    lookup_field = "slug"
    pagination_class = None


class CourseViewSet(viewsets.ModelViewSet):
    """ViewSet for courses."""

    queryset = Course.objects.filter(status=Course.Status.PUBLISHED)
    permission_classes = [AllowAny]
    lookup_field = "slug"
    pagination_class = StandardResultsSetPagination
    filter_backends = [DjangoFilterBackend]
    filterset_fields = ["level", "language", "category", "is_free", "is_featured"]
    search_fields = ["title", "short_description", "description"]
    ordering_fields = ["created_at", "total_students", "total_rating", "price"]

    def get_serializer_class(self):
        if self.action == "list":
            return CourseListSerializer
        if self.action in ["create", "update", "partial_update"]:
            return CourseCreateUpdateSerializer
        return CourseDetailSerializer

    def get_permissions(self):
        if self.action in ["create", "update", "partial_update", "destroy"]:
            return [IsTeacherOrAdmin()]
        return super().get_permissions()

    def get_queryset(self):
        queryset = super().get_queryset()
        
        # Filter by teacher's own courses for authenticated teachers
        if self.request.user.is_authenticated and self.request.user.is_teacher:
            if self.action == "list" and self.request.query_params.get("my_courses"):
                queryset = Course.objects.filter(teacher=self.request.user)
        
        return queryset.select_related("teacher", "category").prefetch_related("tags")

    def retrieve(self, request, *args, **kwargs):
        instance = self.get_object()
        serializer = self.get_serializer(instance)
        return Response({
            "success": True,
            "course": serializer.data,
        })

    @action(detail=False, methods=["get"])
    def featured(self, request):
        """Get featured courses."""
        courses = self.get_queryset().filter(is_featured=True)[:8]
        serializer = CourseListSerializer(courses, many=True, context={"request": request})
        return Response({
            "success": True,
            "courses": serializer.data,
        })

    @action(detail=False, methods=["get"])
    def popular(self, request):
        """Get popular courses."""
        courses = self.get_queryset().filter(is_popular=True)[:8]
        serializer = CourseListSerializer(courses, many=True, context={"request": request})
        return Response({
            "success": True,
            "courses": serializer.data,
        })

    @action(detail=False, methods=["get"])
    def recent(self, request):
        """Get recently published courses."""
        courses = self.get_queryset().order_by("-published_at")[:8]
        serializer = CourseListSerializer(courses, many=True, context={"request": request})
        return Response({
            "success": True,
            "courses": serializer.data,
        })

    @action(detail=True, methods=["get"])
    def reviews(self, request, slug=None):
        """Get course reviews."""
        course = self.get_object()
        reviews = course.reviews.filter(is_approved=True)
        page = self.paginate_queryset(reviews)
        if page is not None:
            serializer = CourseReviewSerializer(page, many=True)
            return self.get_paginated_response(serializer.data)
        serializer = CourseReviewSerializer(reviews, many=True)
        return Response({
            "success": True,
            "reviews": serializer.data,
        })

    @action(detail=False, methods=["get"])
    def my_courses(self, request):
        """Get current user's created courses."""
        if not request.user.is_authenticated:
            return Response({"error": "Authentication required"}, status=401)
        courses = Course.objects.filter(teacher=request.user)
        page = self.paginate_queryset(courses)
        if page is not None:
            serializer = CourseListSerializer(page, many=True, context={"request": request})
            return self.get_paginated_response(serializer.data)
        serializer = CourseListSerializer(courses, many=True, context={"request": request})
        return Response({
            "success": True,
            "courses": serializer.data,
        })


class CourseReviewViewSet(viewsets.ModelViewSet):
    """ViewSet for course reviews."""

    serializer_class = CourseReviewSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        course_id = self.kwargs.get("course_id")
        return CourseReview.objects.filter(
            course_id=course_id,
            is_approved=True,
        ).select_related("user")

    def perform_create(self, serializer):
        course_id = self.kwargs.get("course_id")
        course = Course.objects.get(id=course_id)
        
        # Check if user is enrolled
        if not Enrollment.objects.filter(student=self.request.user, course=course).exists():
            raise serializers.ValidationError("You must be enrolled to review this course.")
        
        # Check if already reviewed
        if CourseReview.objects.filter(course=course, user=self.request.user).exists():
            raise serializers.ValidationError("You have already reviewed this course.")
        
        serializer.save(user=self.request.user, course=course)
        
        # Update course rating
        avg_rating = course.reviews.filter(is_approved=True).aggregate(Avg("rating"))
        course.total_rating = avg_rating["rating__avg"] or 0
        course.total_reviews = course.reviews.filter(is_approved=True).count()
        course.save(update_fields=["total_rating", "total_reviews"])


class EnrollmentViewSet(viewsets.ModelViewSet):
    """ViewSet for enrollments."""

    serializer_class = EnrollmentSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return Enrollment.objects.filter(
            student=self.request.user
        ).select_related("course", "course__teacher", "course__category")

    def get_serializer_class(self):
        if self.action == "create":
            return EnrollmentCreateSerializer
        return EnrollmentSerializer

    def create(self, request, *args, **kwargs):
        serializer = EnrollmentCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        course_id = serializer.validated_data["course_id"]
        expiry_days = serializer.validated_data.get("expiry_days")
        
        course = Course.objects.get(id=course_id)
        
        # Check if already enrolled
        if Enrollment.objects.filter(student=request.user, course=course).exists():
            return Response({
                "success": False,
                "message": "You are already enrolled in this course.",
            }, status=status.HTTP_400_BAD_REQUEST)
        
        # Create enrollment
        enrollment = Enrollment.objects.create(
            student=request.user,
            course=course,
            expiry_date=timezone.now() + timezone.timedelta(days=expiry_days or 365) if expiry_days else None,
        )
        
        # Update course student count
        course.total_students += 1
        course.save(update_fields=["total_students"])
        
        return Response({
            "success": True,
            "message": "Successfully enrolled in course.",
            "enrollment": EnrollmentSerializer(enrollment).data,
        }, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def complete(self, request, pk=None):
        """Mark course as completed."""
        enrollment = self.get_object()
        enrollment.status = Enrollment.Status.COMPLETED
        enrollment.progress = 100
        enrollment.completed_at = timezone.now()
        enrollment.save()
        
        return Response({
            "success": True,
            "message": "Course marked as completed.",
        })

    @action(detail=True, methods=["post"])
    def update_progress(self, request, pk=None):
        """Update course progress."""
        enrollment = self.get_object()
        progress = request.data.get("progress", 0)
        enrollment.progress = min(int(progress), 100)
        
        if enrollment.progress >= 100:
            enrollment.status = Enrollment.Status.COMPLETED
            enrollment.completed_at = timezone.now()
        
        enrollment.save()
        
        return Response({
            "success": True,
            "progress": enrollment.progress,
            "status": enrollment.status,
        })


class WishlistViewSet(viewsets.ModelViewSet):
    """ViewSet for wishlist."""

    serializer_class = WishlistSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return Wishlist.objects.filter(
            student=self.request.user
        ).select_related("course", "course__teacher", "course__category")

    @action(detail=False, methods=["post"])
    def toggle(self, request):
        """Toggle wishlist status for a course."""
        course_id = request.data.get("course_id")
        if not course_id:
            return Response({
                "success": False,
                "message": "Course ID is required.",
            }, status=status.HTTP_400_BAD_REQUEST)
        
        course = Course.objects.get(id=course_id)
        
        wishlist_item, created = Wishlist.objects.get_or_create(
            student=request.user,
            course=course,
        )
        
        if not created:
            wishlist_item.delete()
            return Response({
                "success": True,
                "message": "Removed from wishlist.",
                "in_wishlist": False,
            })
        
        return Response({
            "success": True,
            "message": "Added to wishlist.",
            "in_wishlist": True,
        })


class BookmarkViewSet(viewsets.ModelViewSet):
    """ViewSet for bookmarks."""

    serializer_class = BookmarkSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return Bookmark.objects.filter(
            student=self.request.user
        ).select_related("course", "lesson")

    def create(self, request, *args, **kwargs):
        course_id = request.data.get("course_id")
        lesson_id = request.data.get("lesson_id")
        note = request.data.get("note", "")
        
        course = Course.objects.get(id=course_id)
        lesson = Lesson.objects.get(id=lesson_id)
        
        bookmark, created = Bookmark.objects.get_or_create(
            student=request.user,
            lesson=lesson,
            defaults={"course": course, "note": note},
        )
        
        if not created:
            bookmark.note = note
            bookmark.save()
            return Response({
                "success": True,
                "message": "Bookmark updated.",
            })
        
        return Response({
            "success": True,
            "message": "Bookmark created.",
        }, status=status.HTTP_201_CREATED)
