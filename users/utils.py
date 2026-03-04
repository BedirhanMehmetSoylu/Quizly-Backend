"""
auth/utils.py
─────────────
Helper functions for authentication views.
Business logic is kept here to keep views thin and focused.
"""

from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.exceptions import TokenError


def generate_tokens_for_user(user):
    """Generate and return (access_token, refresh_token) strings for a user."""
    refresh = RefreshToken.for_user(user)
    return str(refresh.access_token), str(refresh)


def set_auth_cookies(response, access_token, refresh_token):
    """Attach JWT access and refresh tokens as HTTP-only cookies to a response."""
    response.set_cookie(
        key="access_token", value=access_token,
        httponly=True, secure=False, samesite="Lax", max_age=15 * 60
    )
    response.set_cookie(
        key="refresh_token", value=refresh_token,
        httponly=True, secure=False, samesite="Lax", max_age=7 * 24 * 60 * 60
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