from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.exceptions import APIException, PermissionDenied, NotFound
from django.conf import settings
from quizzes.models import Quiz, Question
from .serializers import QuizDetailPublicSerializer, QuizDetailSerializer, QuizListSerializer, QuizCreateSerializer, QuizUpdateSerializer
from quizzes.services.quiz_generator import generate_quiz_from_youtube


class QuizCreateView(generics.CreateAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = QuizCreateSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
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


class QuizListView(generics.ListAPIView):
    permission_classes = [permissions.IsAuthenticated]
    serializer_class = QuizListSerializer

    def get_queryset(self):
        return Quiz.objects.filter(user=self.request.user)


class QuizDetailView(generics.RetrieveUpdateDestroyAPIView):
    permission_classes = [permissions.IsAuthenticated]

    def get_queryset(self):
        return Quiz.objects.filter(user=self.request.user)

    def get_serializer_class(self):
        if self.request.method in ["PATCH", "PUT"]:
            return QuizUpdateSerializer
        return QuizDetailPublicSerializer

    def update(self, request, *args, **kwargs):
        partial = kwargs.pop("partial", False)
        instance = self.get_object()

        serializer = QuizUpdateSerializer(
            instance,
            data=request.data,
            partial=partial
        )
        serializer.is_valid(raise_exception=True)
        serializer.save()

        response_serializer = QuizDetailPublicSerializer(instance)

        return Response(
            response_serializer.data,
            status=status.HTTP_200_OK
        )