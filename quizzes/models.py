from django.db import models
from django.contrib.auth.models import User


class Quiz(models.Model):
    """A quiz generated from a YouTube video, belonging to a specific user."""
    title = models.CharField(max_length=255)
    description = models.TextField(blank=True, default="")
    video_url = models.URLField(max_length=500)
    created_by = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="quizzes"
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-created_at"]

    def __str__(self):
        return self.title


class Question(models.Model):
    """A multiple-choice question belonging to a Quiz."""

    quiz = models.ForeignKey(Quiz, on_delete=models.CASCADE, related_name="questions")
    question_title = models.TextField()
    answer = models.CharField(max_length=500)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["id"]

    def __str__(self):
        return self.question_title[:60]


class QuestionOption(models.Model):
    """A single answer option belonging to a Question."""
    
    question = models.ForeignKey(
        Question, on_delete=models.CASCADE, related_name="options"
    )
    text = models.CharField(max_length=500)

    def __str__(self):
        return self.text