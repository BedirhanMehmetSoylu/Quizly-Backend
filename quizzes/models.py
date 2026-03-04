from django.db import models
from django.contrib.auth.models import User


class Quiz(models.Model):
    """
    Represents a quiz generated from a YouTube video.

    A Quiz belongs to a specific user and contains multiple related
    Question instances. It stores metadata such as title, description,
    source video URL, and audit timestamps.
    """
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    video_url = models.URLField(max_length=500)
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="quizzes"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """
        Model configuration options.
        """
        ordering = ["-created_at"]

    def __str__(self):
        """
        Return the human-readable representation of the Quiz.

        Returns:
            str: The quiz title.
        """
        return self.title


class Question(models.Model):
    """
    Represents a single multiple-choice question within a Quiz.

    Each Question:
        - Belongs to exactly one Quiz.
        - Stores the correct answer as plain text.
        - Has multiple associated QuestionOption entries.
    """
    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    question_title = models.TextField()
    answer = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        """
        Model configuration options.
        """
        ordering = ["id"]

    def __str__(self):
        """
        Return a truncated preview of the question text.

        Returns:
            str: The first 60 characters of the question title.
        """
        return self.question_title[:60]


class QuestionOption(models.Model):
    """
    Represents a single answer option for a Question.

    Each QuestionOption:
        - Belongs to exactly one Question.
        - Stores the option text.
    """
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="options"
    )
    text = models.CharField(max_length=500)

    def __str__(self):
        """
        Return the human-readable representation of the option.

        Returns:
            str: The option text.
        """
        return self.text