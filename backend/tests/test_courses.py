import pytest
from django.contrib.auth import get_user_model
from rest_framework import status
from courses.models import Enrollment

User = get_user_model()


@pytest.mark.django_db
class TestCourses:
    def test_list_courses(self, api_client):
        """Test listing courses."""
        response = api_client.get("/api/courses/")
        assert response.status_code == status.HTTP_200_OK

    def test_retrieve_course(self, api_client, course):
        """Test retrieving a course."""
        response = api_client.get(f"/api/courses/{course.slug}/")
        assert response.status_code == status.HTTP_200_OK
        assert response.data["success"] is True
        assert "course" in response.data

    def test_total_students_does_not_increase_on_retrieve(self, course):
        """Test that total_students does not increase on repeated GETs."""
        from courses.models import Course
        initial_count = Course.objects.get(id=course.id).total_students
        
        # Make multiple GET requests
        from rest_framework.test import APIRequestFactory
        from courses.views import CourseViewSet
        for _ in range(5):
            factory = APIRequestFactory()
            request = factory.get(f"/api/courses/{course.slug}/")
            request.user = course.teacher
            
            view = CourseViewSet.as_view({"get": "retrieve"})
            view(request, slug=course.slug)
        
        # Refresh from database
        course.refresh_from_db()
        assert course.total_students == initial_count
