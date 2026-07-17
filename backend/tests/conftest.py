import pytest
from django.contrib.auth import get_user_model
from rest_framework.test import APIClient
from rest_framework_simplejwt.tokens import RefreshToken
from courses.models import Category, Course, Enrollment
from lessons.models import Chapter, Lesson
from quizzes.models import Quiz, Question, Answer
from assignments.models import Assignment, Submission
from notifications.models import UserNotificationSettings

User = get_user_model()


@pytest.fixture
def api_client():
    return APIClient()


@pytest.fixture
def student_user(db):
    user = User.objects.create_user(
        email="student@test.com",
        password="testpass123",
        first_name="Test",
        last_name="Student",
        role=User.Role.STUDENT,
    )
    return user


@pytest.fixture
def teacher_user(db):
    user = User.objects.create_user(
        email="teacher@test.com",
        password="testpass123",
        first_name="Test",
        last_name="Teacher",
        role=User.Role.TEACHER,
    )
    return user


@pytest.fixture
def admin_user(db):
    user = User.objects.create_user(
        email="admin@test.com",
        password="testpass123",
        first_name="Test",
        last_name="Admin",
        role=User.Role.SYSTEM_ADMIN,
        is_staff=True,
    )
    return user


@pytest.fixture
def authenticated_client(api_client, student_user):
    refresh = RefreshToken.for_user(student_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    api_client.user = student_user
    return api_client


@pytest.fixture
def teacher_client(api_client, teacher_user):
    refresh = RefreshToken.for_user(teacher_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    api_client.user = teacher_user
    return api_client


@pytest.fixture
def admin_client(api_client, admin_user):
    refresh = RefreshToken.for_user(admin_user)
    api_client.credentials(HTTP_AUTHORIZATION=f"Bearer {refresh.access_token}")
    api_client.user = admin_user
    return api_client


@pytest.fixture
def category(db):
    return Category.objects.create(
        name="Test Category",
        slug="test-category",
        description="Test Description",
    )


@pytest.fixture
def course(db, teacher_user, category):
    return Course.objects.create(
        title="Test Course",
        slug="test-course",
        teacher=teacher_user,
        category=category,
        short_description="Test Course Short Description",
        description="Test Course Description",
        price=0,
        status=Course.Status.PUBLISHED,
    )


@pytest.fixture
def chapter(db, course):
    return Chapter.objects.create(
        course=course,
        title="Test Chapter",
        order=1,
    )


@pytest.fixture
def lesson(db, course, chapter):
    return Lesson.objects.create(
        course=course,
        chapter=chapter,
        title="Test Lesson",
        slug="test-lesson",
        content="Test Lesson Content",
        order=1,
    )


@pytest.fixture
def quiz(db, course):
    return Quiz.objects.create(
        course=course,
        title="Test Quiz",
        description="Test Quiz Description",
        passing_score=70,
        time_limit=30,
        max_attempts=3,
    )


@pytest.fixture
def question(db, quiz):
    return Question.objects.create(
        quiz=quiz,
        question="What is 2+2?",
        type=Question.Type.MULTIPLE_CHOICE,
        points=10,
    )


@pytest.fixture
def answer(db, question):
    return Answer.objects.create(
        question=question,
        answer="4",
        is_correct=True,
    )


@pytest.fixture
def wrong_answer(db, question):
    return Answer.objects.create(
        question=question,
        answer="5",
        is_correct=False,
    )


@pytest.fixture
def assignment(db, course, lesson):
    return Assignment.objects.create(
        course=course,
        lesson=lesson,
        title="Test Assignment",
        description="Test Assignment Description",
        max_score=100,
        passing_score=70,
        due_date="2030-12-31T23:59:59Z",
    )


@pytest.fixture
def enrollment(db, student_user, course):
    return Enrollment.objects.create(
        student=student_user,
        course=course,
        status=Enrollment.Status.ACTIVE,
    )


@pytest.fixture
def notification_settings(db, student_user):
    return UserNotificationSettings.objects.get_or_create(user=student_user)[0]
