from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.accounts.models import User
from common.test_utils import auth_client, create_user


class RegisterAndLoginTests(APITestCase):
    def test_register_then_login(self):
        response = self.client.post(reverse("auth-register"), {
            "email": "new@example.com",
            "password": "StrongPass123!",
            "first_name": "New",
            "last_name": "User",
        })
        self.assertEqual(response.status_code, status.HTTP_201_CREATED, response.data)
        self.assertTrue(User.objects.filter(email="new@example.com").exists())

        response = self.client.post(reverse("auth-login"), {
            "email": "new@example.com", "password": "StrongPass123!",
        })
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn("access", response.data)
        self.assertIn("refresh", response.data)

    def test_login_with_wrong_password_rejected(self):
        create_user(email="wp@example.com", password="StrongPass123!")
        response = self.client.post(reverse("auth-login"), {
            "email": "wp@example.com", "password": "wrong",
        })
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_requires_auth(self):
        response = self.client.get(reverse("auth-me"))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)

    def test_me_returns_current_user(self):
        user = create_user(email="me@example.com")
        client = auth_client(user)
        response = client.get(reverse("auth-me"))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data["email"], "me@example.com")

    def test_logout_blacklists_refresh_token(self):
        user = create_user(email="lo@example.com", password="StrongPass123!")
        login = self.client.post(reverse("auth-login"), {
            "email": "lo@example.com", "password": "StrongPass123!",
        })
        refresh = login.data["refresh"]
        client = auth_client(user)
        response = client.post(reverse("auth-logout"), {"refresh": refresh})
        self.assertEqual(response.status_code, status.HTTP_205_RESET_CONTENT)

        refresh_response = self.client.post(reverse("auth-refresh"), {"refresh": refresh})
        self.assertEqual(refresh_response.status_code, status.HTTP_401_UNAUTHORIZED)
