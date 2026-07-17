from rest_framework import viewsets, generics, status
from rest_framework.decorators import action
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from django.shortcuts import get_object_or_404
import time

from common.paginations import StandardResultsSetPagination
from courses.models import Course
from lessons.models import Lesson
from .models import ChatSession, ChatMessage, GeneratedContent, AIActivity
from .serializers import (
    ChatSessionSerializer, ChatSessionCreateSerializer,
    SendMessageSerializer, ChatMessageSerializer,
    GenerateQuestionsSerializer, GenerateFlashcardsSerializer,
    SummarizeTextSerializer, ExplainTopicSerializer,
    GrammarCheckSerializer, StudyPlanSerializer,
    GeneratedContentSerializer, AIActivitySerializer,
)
from .providers import get_ai_provider


class ChatSessionViewSet(viewsets.ModelViewSet):
    """ViewSet for chat sessions."""

    serializer_class = ChatSessionSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return ChatSession.objects.filter(
            student=self.request.user,
            is_active=True,
        ).prefetch_related("messages")

    def create(self, request, *args, **kwargs):
        """Create a new chat session and optionally send first message."""
        serializer = ChatSessionCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        course_id = serializer.validated_data.get("course_id")
        title = serializer.validated_data.get("title", "New Chat")
        message_text = serializer.validated_data.get("message", "")
        
        course = None
        if course_id:
            course = get_object_or_404(Course, id=course_id)
        
        session = ChatSession.objects.create(
            student=request.user,
            course=course,
            title=title[:50],
        )
        
        response_data = {
            "success": True,
            "session": ChatSessionSerializer(session).data,
        }
        
        if message_text:
            ai_response = self._send_message(session, message_text, request)
            response_data["response"] = ai_response
        
        return Response(response_data, status=status.HTTP_201_CREATED)

    @action(detail=True, methods=["post"])
    def send_message(self, request, pk=None):
        """Send a message to the AI tutor."""
        session = self.get_object()
        serializer = SendMessageSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        message = serializer.validated_data["message"]
        response_data = self._send_message(session, message, request)
        
        return Response({
            "success": True,
            "session": ChatSessionSerializer(session).data,
            "response": response_data,
        })

    def _send_message(self, session, message_text, request):
        """Send message to AI and save to database."""
        start_time = time.time()
        
        try:
            provider = get_ai_provider()
        except ValueError as e:
            return {"error": str(e)}
        
        # Get conversation history
        history = [
            {"role": "system", "content": self._get_system_prompt(session.course)},
        ]
        for msg in session.messages.order_by("created_at")[-10:]:
            history.append({"role": msg.role, "content": msg.content})
        history.append({"role": "user", "content": message_text})
        
        # Save user message
        user_msg = ChatMessage.objects.create(
            session=session,
            role=ChatMessage.Role.USER,
            content=message_text,
        )
        
        try:
            response_text = provider.chat(history)
            response_time = int((time.time() - start_time) * 1000)
            
            # Save assistant message
            assistant_msg = ChatMessage.objects.create(
                session=session,
                role=ChatMessage.Role.ASSISTANT,
                content=response_text,
                tokens_used=len(response_text.split()) * 2,  # Rough estimate
            )
            
            # Track activity
            AIActivity.objects.create(
                user=request.user,
                activity_type="chat",
                tokens_used=assistant_msg.tokens_used,
                response_time=response_time,
            )
            
            session.updated_at = timezone.now()
            session.save(update_fields=["updated_at"])
            
            return {
                "message_id": assistant_msg.id,
                "content": response_text,
                "tokens_used": assistant_msg.tokens_used,
                "response_time": response_time,
            }
            
        except Exception as e:
            return {"error": str(e)}

    def _get_system_prompt(self, course):
        """Get system prompt based on course context."""
        base_prompt = """You are an AI tutor for an online learning platform called EduShare.
You help students understand topics, answer questions, generate practice problems, and provide educational support.

Guidelines:
- Be helpful, patient, and encouraging
- Explain concepts clearly with examples
- Ask clarifying questions when needed
- Provide step-by-step explanations for complex topics
- Suggest additional resources when appropriate
- Focus on helping students learn, not just giving answers"""
        
        if course:
            base_prompt += f"\n\nYou are currently helping with questions related to the course: {course.title}."
        
        return base_prompt


class AIGeneratorView(generics.GenericAPIView):
    """View for various AI generation endpoints."""

    permission_classes = [IsAuthenticated]

    def post(self, request, action):
        """Handle various AI generation actions."""
        start_time = time.time()
        
        try:
            provider = get_ai_provider()
        except ValueError as e:
            return Response({
                "success": False,
                "error": str(e),
            }, status=status.HTTP_400_BAD_REQUEST)
        
        handlers = {
            "generate_questions": self._generate_questions,
            "generate_flashcards": self._generate_flashcards,
            "summarize": self._summarize,
            "explain": self._explain,
            "grammar_check": self._grammar_check,
            "study_plan": self._study_plan,
        }
        
        if action not in handlers:
            return Response({
                "success": False,
                "error": f"Unknown action: {action}",
            }, status=status.HTTP_404_NOT_FOUND)
        
        return handlers[action](request, provider)

    def _generate_questions(self, request, provider):
        serializer = GenerateQuestionsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        topic = serializer.validated_data["topic"]
        count = serializer.validated_data["count"]
        question_type = serializer.validated_data["question_type"]
        
        try:
            questions = provider.generate_questions(topic, count, question_type)
            response_time = int((time.time() - time.time()) * 1000)
            
            # Save generated content
            course_id = serializer.validated_data.get("course_id")
            lesson_id = serializer.validated_data.get("lesson_id")
            
            if course_id or lesson_id:
                GeneratedContent.objects.create(
                    course_id=course_id,
                    lesson_id=lesson_id,
                    content_type=GeneratedContent.ContentType.QUESTIONS,
                    title=f"Questions about {topic}",
                    content={"topic": topic, "questions": questions},
                    generated_by=request.user,
                )
            
            AIActivity.objects.create(
                user=request.user,
                activity_type="generate_questions",
                response_time=response_time,
            )
            
            return Response({
                "success": True,
                "questions": questions,
            })
            
        except Exception as e:
            return Response({
                "success": False,
                "error": str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _generate_flashcards(self, request, provider):
        serializer = GenerateFlashcardsSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        text = serializer.validated_data["text"]
        count = serializer.validated_data["count"]
        
        try:
            flashcards = provider.generate_flashcards(text, count)
            
            course_id = serializer.validated_data.get("course_id")
            lesson_id = serializer.validated_data.get("lesson_id")
            
            if course_id or lesson_id:
                GeneratedContent.objects.create(
                    course_id=course_id,
                    lesson_id=lesson_id,
                    content_type=GeneratedContent.ContentType.FLASHCARDS,
                    title="Generated Flashcards",
                    content={"flashcards": flashcards},
                    generated_by=request.user,
                )
            
            return Response({
                "success": True,
                "flashcards": flashcards,
            })
            
        except Exception as e:
            return Response({
                "success": False,
                "error": str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _summarize(self, request, provider):
        serializer = SummarizeTextSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        text = serializer.validated_data["text"]
        max_length = serializer.validated_data["max_length"]
        
        try:
            summary = provider.summarize_text(text, max_length)
            
            course_id = serializer.validated_data.get("course_id")
            lesson_id = serializer.validated_data.get("lesson_id")
            
            if course_id or lesson_id:
                GeneratedContent.objects.create(
                    course_id=course_id,
                    lesson_id=lesson_id,
                    content_type=GeneratedContent.ContentType.SUMMARY,
                    title="Generated Summary",
                    content={"summary": summary, "original_length": len(text)},
                    generated_by=request.user,
                )
            
            return Response({
                "success": True,
                "summary": summary,
            })
            
        except Exception as e:
            return Response({
                "success": False,
                "error": str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _explain(self, request, provider):
        serializer = ExplainTopicSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        topic = serializer.validated_data["topic"]
        context = serializer.validated_data.get("context", "")
        
        try:
            explanation = provider.explain_topic(topic, context)
            
            return Response({
                "success": True,
                "topic": topic,
                "explanation": explanation,
            })
            
        except Exception as e:
            return Response({
                "success": False,
                "error": str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _grammar_check(self, request, provider):
        serializer = GrammarCheckSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        text = serializer.validated_data["text"]
        
        try:
            result = provider.check_grammar(text)
            
            return Response({
                "success": True,
                "result": result,
            })
            
        except Exception as e:
            return Response({
                "success": False,
                "error": str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)

    def _study_plan(self, request, provider):
        serializer = StudyPlanSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        
        topic = serializer.validated_data["topic"]
        duration_days = serializer.validated_data["duration_days"]
        
        try:
            plan = provider.generate_study_plan(topic, duration_days)
            
            course_id = serializer.validated_data.get("course_id")
            
            if course_id:
                GeneratedContent.objects.create(
                    course_id=course_id,
                    content_type=GeneratedContent.ContentType.STUDY_PLAN,
                    title=f"Study Plan: {topic}",
                    content=plan,
                    generated_by=request.user,
                )
            
            return Response({
                "success": True,
                "study_plan": plan,
            })
            
        except Exception as e:
            return Response({
                "success": False,
                "error": str(e),
            }, status=status.HTTP_500_INTERNAL_SERVER_ERROR)


class GeneratedContentViewSet(viewsets.ModelViewSet):
    """ViewSet for generated content."""

    serializer_class = GeneratedContentSerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        return GeneratedContent.objects.filter(
            generated_by=self.request.user
        ).select_related("course", "lesson")


class AIActivityViewSet(viewsets.ReadOnlyModelViewSet):
    """ViewSet for AI activity logs (admin only)."""

    serializer_class = AIActivitySerializer
    permission_classes = [IsAuthenticated]
    pagination_class = StandardResultsSetPagination

    def get_queryset(self):
        if self.request.user.is_admin:
            return AIActivity.objects.all()
        return AIActivity.objects.filter(user=self.request.user)
