"""
URL configuration for authentication-related API endpoints.

Defines routes for:
- User registration
- User login
- Token refresh
- User logout

All endpoints are based on class-based views using Django REST Framework.
"""

from django.urls import path
from .views import RegisterView, LoginView, LogoutView, TokenRefreshView

urlpatterns = [
    path('register/', RegisterView.as_view()),
    path('login/', LoginView.as_view()),
    path('logout/', LogoutView.as_view()),
    path('token/refresh/', TokenRefreshView.as_view()),
]