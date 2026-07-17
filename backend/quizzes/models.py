from django.db import models
from django.contrib.auth import get_user_model
from django.utils import timezone
from django.core.validators import MinValueValidator, MaxValueValidator

User = get_user_model()


class Quiz(models.Model):
    """Quiz model."""

    course = models.ForeignKey(
        "courses.Course",
        on_delete=models.CASCADE,
        related_name="quizzes",
    )
    lesson = models.ForeignKey(
        "lessons.Lesson",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="quizzes",
    )
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True)
    
    # Settings
    time_limit = models.IntegerField(
        default=0,
        help_text="Time limit in minutes. 0 means no limit.",
    )
    max_attempts = models.IntegerField(
        default=1,
        validators=[MinValueValidator(1)],
    )
    passing_score = models.IntegerField(
        default=60,
        validators=[MinValueValidator(0), MaxValueValidator(100)],
    )
    max_score = models.IntegerField(default=100)
    
    # Quiz settings
    randomize_questions = models.BooleanField(default=False)
    show_correct_answers = models.BooleanField(default=True)
    show_score = models.BooleanField(default=True)
    is_active = models.BooleanField(default=True)
    
    # Dates
    available_from = models.DateTimeField(null=True, blank=True)
    due_date = models.DateTimeField(null=True, blank=True)
    
    # Statistics
    total_attempts = models.IntegerField(default=0)
    average_score = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    
    # Timestamps
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [
            models.Index(fields=["course", "is_active"]),
            models.Index(fields=["due_date"]),
        ]

    def __str__(self):
        return f"{self.course.title} - {self.title}"

    @property
    def is_available(self):
        now = timezone.now()
        if self.available_from and now < self.available_from:
            return False
        if not self.is_active:
            return False
        return True

    @property
    def total_questions(self):
        return self.questions.count()

    @property
    def total_duration(self):
        """Total duration in minutes considering all questions with individual times."""
        return self.time_limit


class Question(models.Model):
    """Quiz question model."""

    class Type(models.TextChoices):
        MULTIPLE_CHOICE = "multiple_choice", "Multiple Choice"
        TRUE_FALSE = "true_false", "True/False"
        FILL_BLANK = "fill_blank", "Fill in the Blank"
        ESSAY = "essay", "Essay"
        SHORT_ANSWER = "short_answer", "Short Answer"

    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="questions",
    )
    type = models.CharField(
        max_length=20,
        choices=Type.choices,
        default=Type.MULTIPLE_CHOICE,
    )
    question = models.TextField()
    explanation = models.TextField(
        blank=True,
        help_text="Explanation shown after answering.",
    )
    media = models.URLField(blank=True)
    
    # Grading
    points = models.IntegerField(default=1)
    is_required = models.BooleanField(default=True)
    
    # Order
    order = models.IntegerField(default=0)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["quiz", "order", "id"]
        indexes = [models.Index(fields=["quiz", "order"])]

    def __str__(self):
        return f"Q{self.order + 1}: {self.question[:50]}..."


class Answer(models.Model):
    """Answer options for questions."""

    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="answers",
    )
    answer = models.TextField()
    is_correct = models.BooleanField(default=False)
    order = models.IntegerField(default=0)

    class Meta:
        ordering = ["question", "order"]
        verbose_name_plural = "Answers"

    def __str__(self):
        return self.answer


class QuizAttempt(models.Model):
    """Student quiz attempt model."""

    class Status(models.TextChoices):
        IN_PROGRESS = "in_progress", "In Progress"
        COMPLETED = "completed", "Completed"
        GRADED = "graded", "Graded"

    quiz = models.ForeignKey(
        Quiz,
        on_delete=models.CASCADE,
        related_name="attempts",
    )
    student = models.ForeignKey(
        User,
        on_delete=models.CASCADE,
        related_name="quiz_attempts",
    )
    
    # Status and scoring
    status = models.CharField(
        max_length=20,
        choices=Status.choices,
        default=Status.IN_PROGRESS,
    )
    score = models.IntegerField(default=0)
    percentage = models.DecimalField(max_digits=5, decimal_places=2, default=0)
    is_passed = models.BooleanField(default=False)
    
    # Time tracking
    started_at = models.DateTimeField(auto_now_add=True)
    completed_at = models.DateTimeField(null=True, blank=True)
    time_taken = models.IntegerField(default=0)  # in seconds
    
    # Attempt info
    attempt_number = models.IntegerField(default=1)
    ip_address = models.GenericIPAddressField(null=True, blank=True)
    user_agent = models.TextField(blank=True)

    class Meta:
        unique_together = ["quiz", "student", "attempt_number"]
        ordering = ["-started_at"]
        indexes = [
            models.Index(fields=["quiz", "student"]),
            models.Index(fields=["status"]),
        ]

    def __str__(self):
        return f"{self.student} - {self.quiz.title} (Attempt {self.attempt_number})"

    @property
    def can_retake(self):
        return self.quiz.max_attempts > self.attempt_number

    @property
    def questions_answered(self):
        return self.answers.count()


class StudentAnswer(models.Model):
    """Student's answer to a question."""

    attempt = models.ForeignKey(
        QuizAttempt,
        on_delete=models.CASCADE,
        related_name="answers",
    )
    question = models.ForeignKey(
        Question,
        on_delete=models.CASCADE,
        related_name="student_answers",
    )
    
    # Answer data
    selected_answers = models.ManyToManyField(
        Answer,
        blank=True,
        related_name="selected_by",
    )
    text_answer = models.TextField(blank=True)
    
    # Auto-grading
    is_correct = models.BooleanField(default=False)
    points_earned = models.IntegerField(default=0)
    graded_by = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="graded_answers",
    )
    graded_at = models.DateTimeField(null=True, blank=True)
    
    # Feedback
    feedback = models.TextField(blank=True)
    
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = ["attempt", "question"]
        verbose_name_plural = "Student Answers"

    def __str__(self):
        return f"{self.attempt.student} - {self.question}"

    def grade_answer(self):
        """Auto-grade the answer based on question type."""
        if self.question.type == Question.Type.MULTIPLE_CHOICE:
            correct_answers = self.question.answers.filter(is_correct=True)
            selected = set(self.selected_answers.all())
            correct = set(correct_answers)
            self.is_correct = selected == correct
            self.points_earned = self.question.points if self.is_correct else 0
            
        elif self.question.type == Question.Type.TRUE_FALSE:
            correct_answer = self.question.answers.filter(is_correct=True).first()
            if correct_answer and self.selected_answers.exists():
                selected = self.selected_answers.first()
                self.is_correct = selected.id == correct_answer.id
                self.points_earned = self.question.points if self.is_correct else 0
                
        elif self.question.type in [Question.Type.ESSAY, Question.Type.SHORT_ANSWER]:
            # These require manual grading
            self.points_earned = 0
        
        elif self.question.type == Question.Type.FILL_BLANK:
            correct_text = self.question.answers.filter(is_correct=True).first()
            if correct_text and self.text_answer.strip().lower() == correct_text.answer.strip().lower():
                self.is_correct = True
                self.points_earned = self.question.points
            else:
                self.points_earned = 0
        
        self.save()


class QuizResult(models.Model):
    """Detailed quiz result with question-by-question breakdown."""

    attempt = models.OneToOneField(
        QuizAttempt,
        on_delete=models.CASCADE,
        related_name="result",
    )
    correct_answers = models.IntegerField(default=0)
    wrong_answers = models.IntegerField(default=0)
    skipped_questions = models.IntegerField(default=0)
    time_spent = models.IntegerField(default=0)  # in seconds
    
    # Detailed breakdown
    question_details = models.JSONField(default=dict)
    strength_areas = models.JSONField(default=list)
    improvement_areas = models.JSONField(default=list)
    
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        verbose_name_plural = "Quiz Results"

    def __str__(self):
        return f"Result for {self.attempt}"
