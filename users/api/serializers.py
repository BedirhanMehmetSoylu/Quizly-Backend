from django.contrib.auth.models import User
from rest_framework import serializers


class RegisterSerializer(serializers.ModelSerializer):
    """
    Serializer for user registration.

    Extends the default Django User model by adding a
    password confirmation field and validating that both
    passwords match before creating the user instance.
    """

    confirmed_password = serializers.CharField(write_only=True)

    class Meta:
        model = User
        fields = ["username", "email", "password", "confirmed_password"]
        extra_kwargs = {"password": {"write_only": True}}

    def validate_email(self, value):
        """Ensure the email address is not already registered."""
        if User.objects.filter(email=value).exists():
            raise serializers.ValidationError("A user with this email already exists.")
        return value

    def validate(self, data):
        """Validate that password and confirmed_password match."""
        if data["password"] != data["confirmed_password"]:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        """Create a new user with a hashed password."""
        validated_data.pop("confirmed_password")
        return User.objects.create_user(**validated_data)