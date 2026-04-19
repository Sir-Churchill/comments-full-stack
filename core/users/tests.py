from django.test import TestCase
from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework.test import APITestCase
from rest_framework import status

User = get_user_model()


class UserManagerTests(TestCase):
    """Тестирование кастомного менеджера и модели пользователя"""

    def test_create_user_with_email_successful(self):
        email = "test@example.com"
        password = "password123"
        username = "testuser"
        user = User.objects.create_user(
            email=email, password=password, username=username
        )

        self.assertEqual(user.email, email)
        self.assertTrue(user.check_password(password))
        self.assertEqual(user.username, username)
        self.assertFalse(user.is_staff)

    def test_new_user_email_normalized(self):
        email = "TEST@EXAMPLE.COM"
        user = User.objects.create_user(email, "pass123", username="testuser")
        self.assertEqual(user.email, email.lower())

    def test_new_user_invalid_email(self):
        with self.assertRaises(ValueError):
            User.objects.create_user(None, "pass123")

    def test_create_superuser(self):
        user = User.objects.create_superuser(
            "admin@example.com", "pass123", username="admin"
        )
        self.assertTrue(user.is_superuser)
        self.assertTrue(user.is_staff)


class UserApiTests(APITestCase):
    """Тестирование API регистрации и JWT"""

    def test_create_user_success(self):
        payload = {
            "email": "new@example.com",
            "password": "password123",
            "username": "newuser",
            "home_page": "https://google.com",
        }
        res = self.client.post(reverse("register"), payload)

        self.assertEqual(res.status_code, status.HTTP_201_CREATED)
        user = User.objects.get(email=payload["email"])
        self.assertTrue(user.check_password(payload["password"]))
        self.assertNotIn("password", res.data)

    def test_user_exists_error(self):
        payload = {"email": "test@example.com", "password": "pass", "username": "user1"}
        User.objects.create_user(**payload)

        res = self.client.post(reverse("register"), payload)
        self.assertEqual(res.status_code, status.HTTP_400_BAD_REQUEST)

    def test_obtain_token_success(self):
        email = "test@example.com"
        password = "password123"
        User.objects.create_user(email=email, password=password, username="tester")

        payload = {"email": email, "password": password}
        res = self.client.post(reverse("token_obtain_pair"), payload)

        self.assertEqual(res.status_code, status.HTTP_200_OK)
        self.assertIn("access", res.data)
        self.assertIn("refresh", res.data)
