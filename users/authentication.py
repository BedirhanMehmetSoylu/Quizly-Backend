from rest_framework_simplejwt.authentication import JWTAuthentication


class CookieJWTAuthentication(JWTAuthentication):
    """
    Custom JWT authentication class that reads the access token
    from HTTP-only cookies instead of the Authorization header.

    Extends DRF SimpleJWT's JWTAuthentication to support cookie-based JWTs.
    """

    def authenticate(self, request):
        """
        Authenticate the user based on the 'access_token' cookie.

        Parameters:
            request (Request): Incoming HTTP request.

        Returns:
            tuple(User, validated_token): Authenticated user and JWT token
                                          if valid.
            None: If no access token is present in the cookies.

        Notes:
            - This overrides the default header-based JWT authentication.
            - Ensure 'access_token' cookie is set and secure in production.
        """
        access_token = request.COOKIES.get('access_token')

        if not access_token:
            return None

        validated_token = self.get_validated_token(access_token)
        return self.get_user(validated_token), validated_token
