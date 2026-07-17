from rest_framework import serializers
from django.contrib.auth import get_user_model
from .models import Quiz, Question, Answer, QuizAttempt, StudentAnswer, QuizResult

User = get_user_model()


class AnswerSerializer(serializers.ModelSerializer):
    """Serializer for answers."""

    class Meta:
        model = Answer
        fields = ["id", "answer", "order"]


class QuestionSerializer(serializers.ModelSerializer):
    """Serializer for questions."""

    answers = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = [
            "id", "type", "question", "explanation", "media",
            "points", "order", "answers",
        ]

    def get_answers(self, obj):
        if obj.type in [Question.Type.MULTIPLE_CHOICE, Question.Type.TRUE_FALSE]:
            return AnswerSerializer(obj.answers.all(), many=True).data
        elif obj.type == Question.Type.FILL_BLANK:
            return [{"id": None, "answer": "", "order": 0}]
        return []


class QuestionWithAnswersSerializer(QuestionSerializer):
    """Serializer for questions with correct answers (for teachers)."""

    answers = AnswerSerializer(many=True, read_only=True)


class QuizListSerializer(serializers.ModelSerializer):
    """Serializer for quiz list view."""

    total_questions = serializers.IntegerField()
    is_available = serializers.BooleanField()

    class Meta:
        model = Quiz
        fields = [
            "id", "title", "description", "total_questions",
            "time_limit", "max_attempts", "passing_score",
            "is_active", "is_available", "due_date",
        ]


class QuizDetailSerializer(serializers.ModelSerializer):
    """Serializer for quiz detail view."""

    questions_count = serializers.SerializerMethodField()
    user_attempt = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = [
            "id", "title", "description", "time_limit", "max_attempts",
            "passing_score", "max_score", "randomize_questions",
            "show_correct_answers", "show_score", "is_active",
            "available_from", "due_date", "questions_count",
            "user_attempt", "created_at",
        ]

    def get_questions_count(self, obj):
        return obj.questions.count()

    def get_user_attempt(self, obj):
        request = self.context.get("request")
        if request and request.user.is_authenticated:
            attempt = obj.attempts.filter(student=request.user).first()
            if attempt:
                return {
                    "id": attempt.id,
                    "attempt_number": attempt.attempt_number,
                    "status": attempt.status,
                    "score": attempt.score,
                    "percentage": float(attempt.percentage),
                    "can_retake": attempt.can_retake,
                }
        return None


class QuizTakingSerializer(serializers.ModelSerializer):
    """Serializer for taking a quiz (includes questions)."""

    questions = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = [
            "id", "title", "time_limit", "randomize_questions",
            "show_correct_answers", "questions",
        ]

    def get_questions(self, obj):
        request = self.context.get("request")
        questions = obj.questions.all()
        
        if obj.randomize_questions:
            questions = questions.order_by("?")
        
        return QuestionSerializer(questions, many=True, context={"request": request}).data


class QuizCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating quizzes."""

    class Meta:
        model = Quiz
        fields = [
            "title", "description", "lesson", "time_limit", "max_attempts",
            "passing_score", "max_score", "randomize_questions",
            "show_correct_answers", "show_score", "is_active",
            "available_from", "due_date",
        ]


class QuestionCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating questions."""

    class Meta:
        model = Question
        fields = [
            "type", "question", "explanation", "media",
            "points", "is_required", "order",
        ]


class AnswerCreateUpdateSerializer(serializers.ModelSerializer):
    """Serializer for creating/updating answers."""

    class Meta:
        model = Answer
        fields = ["answer", "is_correct", "order"]


class QuizAttemptSerializer(serializers.ModelSerializer):
    """Serializer for quiz attempts."""

    quiz_title = serializers.CharField(source="quiz.title", read_only=True)
    student_name = serializers.SerializerMethodField()

    class Meta:
        model = QuizAttempt
        fields = [
            "id", "quiz", "quiz_title", "student_name", "status",
            "score", "percentage", "is_passed", "started_at",
            "completed_at", "time_taken", "attempt_number",
        ]

    def get_student_name(self, obj):
        return obj.student.get_full_name()


class QuizAttemptDetailSerializer(QuizAttemptSerializer):
    """Serializer for quiz attempt detail with answers."""

    answers = serializers.SerializerMethodField()
    result = serializers.SerializerMethodField()

    class Meta(QuizAttemptSerializer.Meta):
        fields = QuizAttemptSerializer.Meta.fields + ["answers", "result"]

    def get_answers(self, obj):
        answers = obj.answers.select_related("question").prefetch_related("selected_answers")
        return [
            {
                "question_id": a.question.id,
                "question": a.question.question,
                "type": a.question.type,
                "selected_answers": [
                    {"id": sa.id, "answer": sa.answer, "is_correct": sa.is_correct}
                    for sa in a.selected_answers.all()
                ],
                "text_answer": a.text_answer,
                "is_correct": a.is_correct,
                "points_earned": a.points_earned,
                "feedback": a.feedback,
                "correct_answers": [
                    {"id": ca.id, "answer": ca.answer}
                    for ca in a.question.answers.filter(is_correct=True)
                ] if self.context.get("show_answers") else [],
            }
            for a in answers
        ]

    def get_result(self, obj):
        if hasattr(obj, "result"):
            return {
                "correct_answers": obj.result.correct_answers,
                "wrong_answers": obj.result.wrong_answers,
                "skipped_questions": obj.result.skipped_questions,
                "strength_areas": obj.result.strength_areas,
                "improvement_areas": obj.result.improvement_areas,
            }
        return None


class StudentAnswerSerializer(serializers.Serializer):
    """Serializer for submitting student answers."""

    question_id = serializers.IntegerField()
    selected_answers = serializers.ListField(
        child=serializers.IntegerField(),
        required=False,
    )
    text_answer = serializers.CharField(required=False, allow_blank=True)


class QuizSubmissionSerializer(serializers.Serializer):
    """Serializer for submitting quiz answers."""

    answers = StudentAnswerSerializer(many=True)
    time_spent = serializers.IntegerField(required=False, default=0)
