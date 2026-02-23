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
        """
        Serializer configuration.

        Attributes:
            model: The Django User model.
            fields: Fields included in the registration process.
            extra_kwargs: Ensures the password is write-only.
        """
        model = User
        fields = ['username', 'email', 'password', 'confirmed_password']
        extra_kwargs = {'password': {'write_only': True}}

    def validate(self, data):
        """
        Validate that password and confirmed_password match.

        Args:
            data (dict): Incoming validated serializer data.

        Returns:
            dict: Validated data if passwords match.

        Raises:
            ValidationError: If passwords do not match.
        """
        if data['password'] != data['confirmed_password']:
            raise serializers.ValidationError("Passwords do not match.")
        return data

    def create(self, validated_data):
        """
        Create a new user instance with a hashed password.

        Removes the confirmation field and delegates user creation
        to Django's `create_user` method to ensure proper password hashing.

        Args:
            validated_data (dict): Fully validated user data.

        Returns:
            User: The created User instance.
        """
        validated_data.pop('confirmed_password')
        user = User.objects.create_user(**validated_data)
        return user
