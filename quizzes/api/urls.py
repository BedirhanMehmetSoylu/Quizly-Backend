from django.urls import path
from .views import QuizListCreateView, QuizDetailView

urlpatterns = [
    path("quizzes/", QuizListCreateView.as_view()),
    path("quizzes/<int:pk>/", QuizDetailView.as_view()),
]