"""
quiz/urls.py
────────────
URL routing configuration for the quiz application.

Defines REST-style endpoints for listing, creating,
retrieving, updating, and deleting Quiz resources.
"""

from django.urls import path
from .views import QuizListCreateView, QuizDetailView

urlpatterns = [
    path("quizzes/", QuizListCreateView.as_view()),
    path("quizzes/<int:pk>/", QuizDetailView.as_view()),
]
