"""Shared auth helpers for tests in users/ and quizzes/."""

from django.contrib.auth.models import User

PASSWORD = "S3cure-pass-123"


def create_user(username: str = "alice") -> User:
    return User.objects.create_user(username, f"{username}@example.com", PASSWORD)


def login(client, username: str = "alice"):
    """Log in via the API so the client stores the JWT cookies."""
    return client.post("/api/login/", {"username": username, "password": PASSWORD}, format="json")
