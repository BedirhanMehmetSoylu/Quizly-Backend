from rest_framework import serializers
from ..models import Quiz, Question, QuestionOption


class QuestionSerializer(serializers.ModelSerializer):
    """Used in GET responses – no timestamps."""
    question_options = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = ["id", "question_title", "question_options", "answer"]

    def get_question_options(self, obj):
        """
        Return all associated question options as a list of strings.

        Args:
            obj (Question): The Question instance being serialized.

        Returns:
            list[str]: A list containing the text values of all related options.
        """
        return list(obj.options.values_list("text", flat=True))


class QuestionDetailSerializer(serializers.ModelSerializer):
    """Used in POST (create) response – includes timestamps."""
    question_options = serializers.SerializerMethodField()

    class Meta:
        model = Question
        fields = ["id", "question_title", "question_options", "answer", "created_at", "updated_at"]

    def get_question_options(self, obj):
        """
        Return all associated question options as a list of strings.

        Args:
            obj (Question): The Question instance being serialized.

        Returns:
            list[str]: A list containing the text values of all related options.
        """
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


class QuizListSerializer(serializers.ModelSerializer):
    """
    Serializer for listing quizzes.

    Adds a computed field representing the total number
    of related questions.
    """
    question_count = serializers.SerializerMethodField()

    class Meta:
        model = Quiz
        fields = ["id", "title", "description", "created_at", "updated_at", "video_url", "question_count"]

    def get_question_count(self, obj):
        """
        Return the number of questions associated with the quiz.

        Args:
            obj (Quiz): The Quiz instance being serialized.

        Returns:
            int: Total count of related Question objects.
        """
        return obj.questions.count()


class QuizCreateSerializer(serializers.Serializer):
    """
    Serializer used for quiz creation input validation.

    Validates that the provided URL is a valid YouTube watch link.
    """
    url = serializers.URLField()

    def validate_url(self, value):
        """
        Validate that the provided URL is a YouTube watch URL.

        Args:
            value (str): The URL provided in the request payload.

        Returns:
            str: The validated URL.

        Raises:
            ValidationError: If the URL is not a valid YouTube link.
        """
        if "youtube.com/watch" not in value and "youtu.be/" not in value:
            raise serializers.ValidationError("A valid YouTube URL is required.")
        return value


class QuizUpdateSerializer(serializers.ModelSerializer):
    """
    Serializer used for partial updates of a Quiz instance.

    Allows updating the title and/or description fields.
    """
    class Meta:
        model = Quiz
        fields = ["title", "description"]

    def validate_title(self, value):
        """
        Ensure that the title is not an empty string if provided.

        Args:
            value (str): The proposed new title.

        Returns:
            str: The validated title.

        Raises:
            ValidationError: If the title is an empty string.
        """
        if value is not None and value.strip() == "":
            raise serializers.ValidationError("Title cannot be blank.")
        return value

    def validate(self, data):
        """
        Ensure that at least one updatable field is provided.

        Args:
            data (dict): Incoming validated data.

        Returns:
            dict: The validated data.

        Raises:
            ValidationError: If no fields are provided for update.
        """
        if not data:
            raise serializers.ValidationError("At least one field (title or description) must be provided.")
        return data