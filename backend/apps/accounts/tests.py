from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase


class AuthAPITests(APITestCase):
    def test_register_user(self):
        payload = {
            'email': 'alice@example.com',
            'password': 'StrongPass123',
            'first_name': 'Alice',
            'last_name': 'Smith',
        }
        response = self.client.post(reverse('register'), payload, format='json')
        self.assertEqual(response.status_code, status.HTTP_201_CREATED)
        self.assertIn('token', response.data)
        self.assertEqual(response.data['user']['email'], 'alice@example.com')

    def test_login_user(self):
        self.client.post(
            reverse('register'),
            {
                'email': 'bob@example.com',
                'password': 'StrongPass123',
                'first_name': 'Bob',
                'last_name': 'Jones',
            },
            format='json',
        )
        response = self.client.post(
            reverse('token_obtain_pair'),
            {'email': 'bob@example.com', 'password': 'StrongPass123'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('access', response.data)

    def test_auth_me_requires_login(self):
        response = self.client.get(reverse('me'))
        self.assertEqual(response.status_code, status.HTTP_401_UNAUTHORIZED)
