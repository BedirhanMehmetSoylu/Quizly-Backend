from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import APIException, PermissionDenied, NotFound
from django.conf import settings
from quizzes.models import Quiz, Question
from .serializers import QuizDetailPublicSerializer, QuizDetailSerializer, QuizListSerializer, QuizSerializer, QuizCreateSerializer
from quizzes.services.quiz_generator import generate_quiz_from_youtube


class QuizListCreateView(generics.ListCreateAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Quiz.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method == "POST":
            return QuizDetailSerializer
        return QuizListSerializer

    def create(self, request, *args, **kwargs):
        serializer = QuizCreateSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        video_url = serializer.validated_data["url"]

        if not settings.GEMINI_API_KEY:
            raise APIException("GEMINI_API_KEY is not configured.")

        try:
            quiz_data = generate_quiz_from_youtube(video_url)
        except Exception as e:
            raise APIException(f"Quiz generation failed: {str(e)}")

        quiz = Quiz.objects.create(
            user=request.user,
            title=quiz_data["title"],
            description=quiz_data["description"],
            video_url=video_url,
        )

        questions = [
            Question(
                quiz=quiz,
                question_title=q["question_title"],
                question_options=q["question_options"],
                answer=q["answer"],
            )
            for q in quiz_data["questions"]
        ]

        Question.objects.bulk_create(questions)

        return Response(
            QuizDetailSerializer(quiz).data,
            status=status.HTTP_201_CREATED
        )


class QuizDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = QuizDetailPublicSerializer

    def get_queryset(self):
        return Quiz.objects.all()

    def get_object(self):
        obj = super().get_object()

        if obj.user != self.request.user:
            raise PermissionDenied("Access denied - Quiz belongs to another user.")

        return obj

