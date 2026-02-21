from django.urls import path
from .views import QuizListView, QuizCreateView, QuizDetailView

urlpatterns = [
    path("quizzes/", QuizListView.as_view()),
    path("createQuiz/", QuizCreateView.as_view()),
    path("quizzes/<int:pk>/", QuizDetailView.as_view()),
]