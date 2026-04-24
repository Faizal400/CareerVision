from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse


class AuthTests(TestCase):
    """Registration, login, and protected routes."""

    def setUp(self):
        self.client = Client()

    def test_register_creates_user_and_logs_in(self):
        response = self.client.post(reverse("register"), {
            "username": "newuser",
            "password1": "complexpass123!",
            "password2": "complexpass123!",
        })
        self.assertTrue(User.objects.filter(username="newuser").exists())

    def test_login_with_valid_credentials(self):
        User.objects.create_user(username="testuser", password="testpass123")
        response = self.client.post(reverse("login"), {
            "username": "testuser",
            "password": "testpass123",
        })
        # Should redirect after successful login
        self.assertEqual(response.status_code, 302)

    def test_login_with_wrong_password_fails(self):
        User.objects.create_user(username="testuser", password="testpass123")
        response = self.client.post(reverse("login"), {
            "username": "testuser",
            "password": "wrongpassword",
        })
        # Should stay on login page (200) not redirect
        self.assertEqual(response.status_code, 200)

    def test_home_requires_login(self):
        response = self.client.get(reverse("home"))
        self.assertEqual(response.status_code, 302)

    def test_profile_requires_login(self):
        response = self.client.get(reverse("profile"))
        self.assertRedirects(response, "/accounts/login/?next=/accounts/profile/")

    def test_cv_matcher_requires_login(self):
        response = self.client.get(reverse("cv_matcher_ingest"))
        self.assertRedirects(response, "/accounts/login/?next=/cv-matcher/")
