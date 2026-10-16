from django.test import TestCase, Client
from django.contrib.auth.models import User
from django.urls import reverse

class DashboardPermissionsTestCase(TestCase):
    def setUp(self):
        self.client = Client()
        self.normal_user = User.objects.create_user(
            username='cliente',
            password='password123',
            is_staff=False
        )
        self.staff_user = User.objects.create_user(
            username='staff_daca',
            password='password123',
            is_staff=True
        )

    def test_anonymous_user_redirected(self):
        response = self.client.get(reverse('dashboard:home'))
        self.assertEqual(response.status_code, 302)

    def test_normal_user_forbidden(self):
        self.client.login(username='cliente', password='password123')
        response = self.client.get(reverse('dashboard:home'))
        self.assertEqual(response.status_code, 403)

    def test_staff_user_allowed(self):
        self.client.login(username='staff_daca', password='password123')
        response = self.client.get(reverse('dashboard:home'))
        self.assertEqual(response.status_code, 200)
        self.assertContains(response, "Panel de Control")
