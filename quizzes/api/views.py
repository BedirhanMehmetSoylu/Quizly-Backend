"""
API views for quiz management.
All views return HTTP responses only – business logic lives in utils.py.
"""

from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView

from ..models import Quiz
from .serializers import (
    QuizCreateSerializer,
    QuizSerializer,
    QuizCreateResponseSerializer,
    QuizUpdateSerializer,
)
from ..utils import create_quiz_from_youtube


class QuizListCreateView(APIView):
    """
    GET  /api/quizzes/  – List all quizzes of the logged-in user.
    POST /api/quizzes/  – Create a quiz from a YouTube URL.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Return all quizzes belonging to the authenticated user."""
        quizzes = Quiz.objects.filter(created_by=request.user)
        return Response(QuizSerializer(quizzes, many=True).data)

    def post(self, request):
        """Validate the URL, run the pipeline, return the created quiz."""
        serializer = QuizCreateSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        return _handle_quiz_creation(serializer.validated_data["url"], request.user)


class QuizDetailView(APIView):
    """
    GET    /api/quizzes/{id}/  – Retrieve a quiz with questions.
    PATCH  /api/quizzes/{id}/  – Update title and/or description.
    DELETE /api/quizzes/{id}/  – Delete the quiz.
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, pk):
        """Return a single quiz with all questions and options."""
        quiz, error = _get_quiz_or_error(pk, request.user)
        if error:
            return error
        return Response(QuizSerializer(quiz).data)

    def patch(self, request, pk):
        """Partially update title and/or description of a quiz."""
        quiz, error = _get_quiz_or_error(pk, request.user)
        if error:
            return error
        serializer = QuizUpdateSerializer(quiz, data=request.data, partial=True)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response(QuizSerializer(quiz).data)

    def delete(self, request, pk):
        """Delete a quiz and all its related questions."""
        quiz, error = _get_quiz_or_error(pk, request.user)
        if error:
            return error
        quiz.delete()
        return Response(status=status.HTTP_204_NO_CONTENT)


def _get_quiz_or_error(pk: int, user):
    """Return (quiz, None) or (None, error_response) for ownership checks."""
    try:
        quiz = Quiz.objects.get(pk=pk)
    except Quiz.DoesNotExist:
        return None, Response({"detail": "Quiz not found."}, status=status.HTTP_404_NOT_FOUND)
    if quiz.created_by != user:
        return None, Response({"detail": "Access denied."}, status=status.HTTP_403_FORBIDDEN)
    return quiz, None


def _handle_quiz_creation(youtube_url: str, user):
    """Run the full pipeline and return the appropriate HTTP response."""
    try:
        quiz = create_quiz_from_youtube(youtube_url, user)
    except ValueError as exc:
        return Response({"detail": str(exc)}, status=status.HTTP_422_UNPROCESSABLE_ENTITY)
    except Exception as exc:
        return Response({"detail": f"Unexpected error: {exc}"}, status=status.HTTP_500_INTERNAL_SERVER_ERROR)
    return Response(QuizCreateResponseSerializer(quiz).data, status=status.HTTP_201_CREATED)