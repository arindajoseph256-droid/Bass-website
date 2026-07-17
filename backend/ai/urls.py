from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ChatSessionViewSet, AIGeneratorView, GeneratedContentViewSet, AIActivityViewSet

router = DefaultRouter()
router.register("sessions", ChatSessionViewSet, basename="chat-session")
router.register("content", GeneratedContentViewSet, basename="generated-content")
router.register("activities", AIActivityViewSet, basename="ai-activity")

urlpatterns = [
    path("generate/<str:action>/", AIGeneratorView.as_view(), name="ai-generator"),
    path("", include(router.urls)),
]
