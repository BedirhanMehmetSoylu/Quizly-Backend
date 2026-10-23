"""Tests for registration, login, token refresh and logout."""

from datetime import timedelta

from django.contrib.auth.models import User
from rest_framework import status
from rest_framework.test import APITestCase
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework_simplejwt.tokens import AccessToken

from .helpers import PASSWORD, create_user, login

ACCESS_MAX_AGE = 30 * 60
REFRESH_MAX_AGE = 7 * 24 * 60 * 60


def expired_access_token(user) -> str:
    token = AccessToken.for_user(user)
    token.set_exp(lifetime=timedelta(seconds=-1))
    return str(token)


class RegisterTests(APITestCase):
    url = "/api/register/"

    def _payload(self, **overrides):
        data = {
            "username": "bob",
            "email": "bob@example.com",
            "password": PASSWORD,
            "confirmed_password": PASSWORD,
        }
        data.update(overrides)
        return data

    def test_register_creates_user(self):
        response = self.client.post(self.url, self._payload(), format="json")
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(username="bob")
        self.assertTrue(user.check_password(PASSWORD))

    def test_register_rejects_mismatched_passwords(self):
        response = self.client.post(self.url, self._payload(confirmed_password="other"), format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertFalse(User.objects.filter(username="bob").exists())

    def test_register_rejects_duplicate_email(self):
        create_user("alice")
        response = self.client.post(self.url, self._payload(email="alice@example.com"), format="json")
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)
        self.assertIn("email", response.data)


class LoginTests(APITestCase):
    def setUp(self):
        self.user = create_user("alice")

    def test_login_sets_http_only_cookies(self):
        response = login(self.client)
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["user"]["username"], "alice")
        access = response.cookies["access_token"]
        refresh = response.cookies["refresh_token"]
        self.assertTrue(access.value)
        self.assertTrue(refresh.value)
        self.assertTrue(access["httponly"])
        self.assertTrue(refresh["httponly"])
        self.assertEqual(access["max-age"], ACCESS_MAX_AGE)
        self.assertEqual(refresh["max-age"], REFRESH_MAX_AGE)

    def test_login_does_not_return_tokens_in_body(self):
        response = login(self.client)
        self.assertNotIn("access", response.data)
        self.assertNotIn("refresh", response.data)

    def test_login_with_wrong_password_returns_401(self):
        response = self.client.post(
            "/api/login/", {"username": "alice", "password": "wrong"}, format="json"
        )
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
        self.assertNotIn("access_token", response.cookies)


class TokenRefreshTests(APITestCase):
    def setUp(self):
        create_user("alice")

    def test_refresh_sets_new_access_cookie(self):
        login(self.client)
        response = self.client.post("/api/token/refresh/")
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.cookies["access_token"]["max-age"], ACCESS_MAX_AGE)

    def test_refresh_without_cookie_returns_401(self):
        response = self.client.post("/api/token/refresh/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)


class LogoutTests(APITestCase):
    def setUp(self):
        create_user("alice")

    def test_logout_blacklists_refresh_token_and_clears_cookies(self):
        refresh_token = login(self.client).cookies["refresh_token"].value

        response = self.client.post("/api/logout/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(BlacklistedToken.objects.count(), 1)
        self.assertEqual(response.cookies["access_token"].value, "")
        self.assertEqual(response.cookies["refresh_token"].value, "")

        # The old refresh token must no longer issue new access tokens.
        self.client.cookies["refresh_token"] = refresh_token
        response = self.client.post("/api/token/refresh/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_with_expired_access_cookie_still_blacklists_refresh_token(self):
        refresh_token = login(self.client).cookies["refresh_token"].value
        # The browser drops the access cookie once its max-age has passed.
        del self.client.cookies["access_token"]

        response = self.client.post("/api/logout/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(BlacklistedToken.objects.count(), 1)
        self.assertEqual(response.cookies["access_token"].value, "")
        self.assertEqual(response.cookies["refresh_token"].value, "")

        self.client.cookies["refresh_token"] = refresh_token
        response = self.client.post("/api/token/refresh/")
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_logout_with_invalid_access_cookie_still_succeeds(self):
        login(self.client)
        self.client.cookies["access_token"] = "not-a-jwt"

        response = self.client.post("/api/logout/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(BlacklistedToken.objects.count(), 1)

    def test_logout_without_cookies_succeeds_without_blacklisting(self):
        response = self.client.post("/api/logout/")

        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(OutstandingToken.objects.count(), 0)
        self.assertEqual(BlacklistedToken.objects.count(), 0)


class StaleAccessCookieTests(APITestCase):
    """Public auth endpoints must ignore an invalid or expired access cookie."""

    def setUp(self):
        self.user = create_user("alice")
        self.stale_cookies = {
            "invalid": "not-a-jwt",
            "expired": expired_access_token(self.user),
        }

    def test_register_ignores_stale_access_cookie(self):
        for kind, cookie in self.stale_cookies.items():
            with self.subTest(kind=kind):
                self.client.cookies["access_token"] = cookie
                response = self.client.post(
                    "/api/register/",
                    {
                        "username": f"bob_{kind}",
                        "email": f"bob_{kind}@example.com",
                        "password": PASSWORD,
                        "confirmed_password": PASSWORD,
                    },
                    format="json",
                )
                self.assertEqual(response.status_code, status.HTTP_201_CREATED)

    def test_login_ignores_stale_access_cookie(self):
        for kind, cookie in self.stale_cookies.items():
            with self.subTest(kind=kind):
                self.client.cookies["access_token"] = cookie
                response = login(self.client)
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertTrue(response.cookies["access_token"].value)

    def test_refresh_ignores_stale_access_cookie(self):
        for kind, cookie in self.stale_cookies.items():
            with self.subTest(kind=kind):
                login(self.client)
                self.client.cookies["access_token"] = cookie
                response = self.client.post("/api/token/refresh/")
                self.assertEqual(response.status_code, status.HTTP_200_OK)
                self.assertEqual(response.cookies["access_token"]["max-age"], ACCESS_MAX_AGE)

    def test_protected_endpoints_still_reject_stale_access_cookie(self):
        for kind, cookie in self.stale_cookies.items():
            with self.subTest(kind=kind):
                self.client.cookies["access_token"] = cookie
                response = self.client.get("/api/quizzes/")
                self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
