from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework.permissions import IsAuthenticated
from rest_framework_simplejwt.tokens import RefreshToken
from .serializers import RegisterSerializer
from ..utils import generate_tokens_for_user


class RegisterView(APIView):
    """
    API endpoint for user registration.

    Accepts user credentials via POST request, validates the input
    using RegisterSerializer, and creates a new user instance.

    Returns:
        201 Created: If the user was successfully created.
        400 Bad Request: If validation fails.
    """

    def post(self, request):
        """
        Handle user registration.

        Args:
            request (Request): Incoming HTTP request containing user data.

        Returns:
            Response: JSON response with status message.
        """
        serializer = RegisterSerializer(data=request.data)

        if not serializer.is_valid():
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)

        serializer.save()
        return Response(
            {"detail": "User created successfully!"},
            status=status.HTTP_201_CREATED
        )


class LoginView(APIView):
    """
    API endpoint for user authentication.

    Authenticates user credentials and issues JWT access and refresh tokens.
    Tokens are stored in HTTP-only cookies for improved security.

    Returns:
        200 OK: If authentication succeeds.
        401 Unauthorized: If credentials are invalid.
    """

    def post(self, request):
        """
        Handle user login.

        Args:
            request (Request): Incoming HTTP request containing
                               'username' and 'password'.

        Returns:
            Response: JSON response with user information and cookies set.
        """
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(username=username, password=password)

        if not user:
            return Response(
                {"detail": "Invalid credentials."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        access_token, refresh_token = generate_tokens_for_user(user)

        response = Response(
            {
                "detail": "Login successfully!",
                "user": {
                    "id": user.id,
                    "username": user.username,
                    "email": user.email,
                }
            },
            status=status.HTTP_200_OK
        )

        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            samesite="Lax"
        )

        response.set_cookie(
            key="refresh_token",
            value=refresh_token,
            httponly=True,
            samesite="Lax"
        )

        return response


class TokenRefreshView(APIView):
    """
    API endpoint for refreshing JWT access tokens.

    Reads the refresh token from HTTP-only cookies and issues a new
    access token if the refresh token is valid.

    Returns:
        200 OK: If a new access token was successfully issued.
        401 Unauthorized: If the refresh token is missing or invalid.
    """

    def post(self, request):
        """
        Handle token refresh.

        Args:
            request (Request): Incoming HTTP request containing
                               refresh token in cookies.

        Returns:
            Response: JSON response with updated access token cookie.
        """
        refresh_token = request.COOKIES.get("refresh_token")

        if not refresh_token:
            return Response(
                {"detail": "Refresh token invalid or missing."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        try:
            refresh = RefreshToken(refresh_token)
            access_token = str(refresh.access_token)
        except Exception:
            return Response(
                {"detail": "Invalid refresh token."},
                status=status.HTTP_401_UNAUTHORIZED
            )

        response = Response({"detail": "Token refreshed"}, status=status.HTTP_200_OK)
        response.set_cookie(
            key="access_token",
            value=access_token,
            httponly=True,
            samesite="Lax"
        )
        return response


class LogoutView(APIView):
    """
    API endpoint for user logout.

    Requires authentication. Blacklists the refresh token (if present)
    and removes authentication cookies from the client.

    Returns:
        200 OK: If logout process completes.
    """

    permission_classes = [IsAuthenticated]

    def post(self, request):
        """
        Handle user logout.

        Args:
            request (Request): Authenticated HTTP request.

        Returns:
            Response: JSON response confirming logout and cookie removal.
        """
        refresh_token = request.COOKIES.get("refresh_token")

        if refresh_token:
            try:
                token = RefreshToken(refresh_token)
                token.blacklist()
            except Exception:
                pass

        response = Response(
            {"detail": "Log-Out successfully! All Tokens will be deleted. Refresh token is now invalid."},
            status=status.HTTP_200_OK
        )

        response.delete_cookie("access_token")
        response.delete_cookie("refresh_token")

        return response