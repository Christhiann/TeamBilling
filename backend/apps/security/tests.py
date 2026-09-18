from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase
import pyotp

User = get_user_model()


class SecurityAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(email='security@example.com', password='StrongPass123')
        self.client.force_authenticate(user=self.user)

    def test_setup_2fa_returns_secret(self):
        response = self.client.post(reverse('twofactor-setup'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('secret', response.data)
        self.assertIn('otpauth_url', response.data)

    def test_verify_valid_code_enables_2fa(self):
        response = self.client.post(reverse('twofactor-setup'))
        secret = response.data['secret']
        code = pyotp.TOTP(secret).now()
        response = self.client.post(reverse('twofactor-verify'), {'code': code}, format='json')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertTrue(self.user.two_factor_enabled)

    def test_invalid_code_is_rejected(self):
        self.client.post(reverse('twofactor-setup'))
        response = self.client.post(reverse('twofactor-verify'), {'code': '000000'}, format='json')
        self.assertEqual(response.status_code, status.HTTP_400_BAD_REQUEST)

    def test_disable_2fa_resets_flags(self):
        self.client.post(reverse('twofactor-setup'))
        secret = self.user.two_factor_setup.secret
        code = pyotp.TOTP(secret).now()
        self.client.post(reverse('twofactor-verify'), {'code': code}, format='json')
        response = self.client.post(reverse('twofactor-disable'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.user.refresh_from_db()
        self.assertFalse(self.user.two_factor_enabled)
