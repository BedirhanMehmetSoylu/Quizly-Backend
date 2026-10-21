"""
Helper functions for authentication views.
Business logic is kept here to keep views thin and focused.
"""

from rest_framework_simplejwt.settings import api_settings
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError


def generate_tokens_for_user(user):
    """Generate and return (access_token, refresh_token) strings for a user."""
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token), str(refresh)


def set_access_cookie(response, access_token):
    """Attach the access token as an HTTP-only cookie matching ACCESS_TOKEN_LIFETIME."""
    response.set_cookie(
        key="access_token", value=access_token,
        httponly=True, secure=False, samesite="Lax",
        max_age=int(api_settings.ACCESS_TOKEN_LIFETIME.total_seconds()),
    )


def set_auth_cookies(response, access_token, refresh_token):
    """Attach JWT access and refresh tokens as HTTP-only cookies to a response."""
    set_access_cookie(response, access_token)
    response.set_cookie(
        key="refresh_token", value=refresh_token,
        httponly=True, secure=False, samesite="Lax",
        max_age=int(api_settings.REFRESH_TOKEN_LIFETIME.total_seconds()),
    )


def delete_auth_cookies(response):
    """Remove JWT cookies from the response on logout."""
    response.delete_cookie("access_token")
    response.delete_cookie("refresh_token")


def blacklist_refresh_token(refresh_token: str) -> None:
    """Blacklist a refresh token string. Silently ignores invalid tokens."""
    try:
        RefreshToken(refresh_token).blacklist()
    except TokenError:
        pass


def refresh_access_token(refresh_token: str) -> str:
    """Return a new access token string from a valid refresh token."""
    return str(RefreshToken(refresh_token).access_token)


def build_user_payload(user) -> dict:
    """Return a serializable dict of basic user info for the login response."""
    return {"id": user.id, "username": user.username, "email": user.email}