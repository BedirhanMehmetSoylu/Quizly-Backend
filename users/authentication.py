from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieJWTAuthentication(JWTAuthentication):
    """Reads the JWT access token from HTTP-only cookies instead of the Authorization header."""

    def authenticate(self, request):
        """Return authenticated user from access_token cookie, or None if missing."""
        access_token = request.COOKIES.get('access_token')

        if not access_token:
            return None

        validated_token = self.get_validated_token(access_token)
        return self.get_user(validated_token), validated_token
