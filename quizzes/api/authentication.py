from rest_framework_simplejwt.authentication import JWTAuthentication

class CookieJWTAuthentication(JWTAuthentication):
    """
    Custom JWT auth for reading access token from HTTP-only cookie.
    """
    def authenticate(self, request):
        """
        Authenticate the incoming request using a JWT stored in a cookie.

        Args:
            request (HttpRequest): The incoming HTTP request object.

        Returns:
            tuple[User, Token] | None:
                - A tuple containing the authenticated user instance and the validated token
                  if authentication succeeds.
                - None if no access token cookie is present.

        Raises:
            AuthenticationFailed:
                If the token is present but invalid or expired.
        """
        raw_token = request.COOKIES.get("access_token")
        if raw_token is None:
            return None
        validated_token = self.get_validated_token(raw_token)
        return self.get_user(validated_token), validated_token