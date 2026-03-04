"""
auth/views.py
─────────────
API views for user authentication using JWT and HTTP-only cookies.
All business logic lives in utils.py – views only handle HTTP in/out.
"""

from django.contrib.auth import authenticate
from rest_framework import status
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.exceptions import TokenError

from .serializers import RegisterSerializer
from ..utils import (
    generate_tokens_for_user,
    set_auth_cookies,
    delete_auth_cookies,
    blacklist_refresh_token,
    refresh_access_token,
    build_user_payload,
)


class RegisterView(APIView):
    """Register a new user account."""

    def post(self, request):
        """Validate input and create a new user. Returns 201 on success."""
        serializer = RegisterSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        serializer.save()
        return Response({"detail": "User created successfully!"}, status=status.HTTP_201_CREATED)


class LoginView(APIView):
    """Authenticate a user and issue JWT tokens via HTTP-only cookies."""

    def post(self, request):
        """Validate credentials and set auth cookies. Returns 200 on success."""
        user = authenticate(
            username=request.data.get("username"),
            password=request.data.get("password"),
        )
        if not user:
            return Response({"detail": "Invalid credentials."}, status=status.HTTP_401_UNAUTHORIZED)
        return _build_login_response(user)


class TokenRefreshView(APIView):
    """Issue a new access token from the refresh token cookie."""

    def post(self, request):
        """Read refresh cookie, validate it, and return a new access token cookie."""
        refresh_token = request.COOKIES.get("refresh_token")
        if not refresh_token:
            return Response({"detail": "Refresh token missing."}, status=status.HTTP_401_UNAUTHORIZED)
        try:
            new_access_token = refresh_access_token(refresh_token)
        except TokenError:
            return Response({"detail": "Invalid refresh token."}, status=status.HTTP_401_UNAUTHORIZED)
        response = Response({"detail": "Access token refreshed."}, status=status.HTTP_200_OK)
        response.set_cookie(
            key="access_token", value=new_access_token,
            httponly=True, secure=False, samesite="Lax", max_age=15 * 60
        )
        return response


class LogoutView(APIView):
    """Blacklist the refresh token and clear auth cookies."""

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """Blacklist refresh token and delete both auth cookies."""
        blacklist_refresh_token(request.COOKIES.get("refresh_token"))
        response = Response({"detail": "Logged out successfully."}, status=status.HTTP_200_OK)
        delete_auth_cookies(response)
        return response
    

def _build_login_response(user) -> Response:
    """Build a 200 response with user info and set auth cookies."""
    access_token, refresh_token = generate_tokens_for_user(user)
    response = Response(
        {"detail": "Login successful.", "user": build_user_payload(user)},
        status=status.HTTP_200_OK,
    )
    set_auth_cookies(response, access_token, refresh_token)
    return response