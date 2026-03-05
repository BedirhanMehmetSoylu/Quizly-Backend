from rest_framework import serializers
from ..models import Quiz, Question, QuestionOption


class QuestionSerializer(serializers.ModelSerializer):
    """Used in GET responses – no timestamps."""
    question_options = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = ["id", "question_title", "question_options", "answer"]

    def get_question_options(self, obj):
        """Return all answer options as a list of strings."""
        return list(obj.options.values_list("text", flat=True))


class QuestionDetailSerializer(serializers.ModelSerializer):
    """Used in POST (create) response – includes timestamps."""
    question_options = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = ["id", "question_title", "question_options", "answer", "created_at", "updated_at"]

    def get_question_options(self, obj):
        """Return all answer options as a list of strings."""
        return list(obj.options.values_list("text", flat=True))


class QuizSerializer(serializers.ModelSerializer):
    """Used in GET responses – questions without timestamps."""
    questions = QuestionSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = ["id", "title", "description", "created_at", "updated_at", "video_url", "questions"]


class QuizCreateResponseSerializer(serializers.ModelSerializer):
    """Used in POST (create) response – questions with timestamps."""
    questions = QuestionDetailSerializer(many=True, read_only=True)

    class Meta:
        model = Quiz
        fields = ["id", "title", "description", "created_at", "updated_at", "video_url", "questions"]


class QuizCreateSerializer(serializers.Serializer):
    """Validates the YouTube URL for quiz creation."""
    
    url = serializers.URLField()

    def validate_url(self, value):
        """Reject URLs that are not valid YouTube links."""
        if "youtube.com/watch" not in value and "youtu.be/" not in value:
            raise serializers.ValidationError("A valid YouTube URL is required.")
        return value


class QuizUpdateSerializer(serializers.ModelSerializer):
    """Validates partial updates of title and/or description."""

    class Meta:
        model = Quiz
        fields = ["title", "description"]

    def validate_title(self, value):
        """Reject empty title strings."""
        if value is not None and value.strip() == "":
            raise serializers.ValidationError("Title cannot be blank.")
        return value

    def validate(self, data):
        """Require at least one field to be provided."""
        if not data:
            raise serializers.ValidationError("At least one field (title or description) must be provided.")
        return data