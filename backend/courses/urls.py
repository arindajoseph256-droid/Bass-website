from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import (
    CategoryViewSet, TagViewSet, CourseViewSet,
    CourseReviewViewSet, EnrollmentViewSet,
    WishlistViewSet, BookmarkViewSet,
)

router = DefaultRouter()
router.register("categories", CategoryViewSet, basename="category")
router.register("tags", TagViewSet, basename="tag")
router.register("", CourseViewSet, basename="course")
router.register("enrollments", EnrollmentViewSet, basename="enrollment")
router.register("wishlist", WishlistViewSet, basename="wishlist")
router.register("bookmarks", BookmarkViewSet, basename="bookmark")

urlpatterns = [
    path("", include(router.urls)),
    path("<int:course_id>/reviews/", CourseReviewViewSet.as_view({"get": "list", "post": "create"}), name="course-reviews"),
]
