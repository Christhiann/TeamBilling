from django.contrib.auth import get_user_model
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from .models import Membership, Organization

User = get_user_model()


class OrganizationAPITests(APITestCase):
    def setUp(self):
        self.user = User.objects.create_user(
            email='owner@example.com',
            password='StrongPass123',
            first_name='Owner',
            last_name='User',
        )
        self.other_user = User.objects.create_user(
            email='other@example.com',
            password='StrongPass123',
            first_name='Other',
            last_name='User',
        )
        self.organization = Organization.objects.create(name='Acme', slug='acme')
        Membership.objects.create(user=self.user, organization=self.organization, role=Membership.Role.OWNER)
        self.other_org = Organization.objects.create(name='Beta', slug='beta')
        Membership.objects.create(user=self.other_user, organization=self.other_org, role=Membership.Role.OWNER)

    def test_user_can_list_own_organization(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('organizations-list-create'))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data[0]['name'], 'Acme')

    def test_user_cannot_access_other_organization_by_id(self):
        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('organization-detail', args=[self.other_org.id]))
        self.assertEqual(response.status_code, status.HTTP_404_NOT_FOUND)

    def test_member_can_view_but_not_manage_organization(self):
        member = User.objects.create_user(email='member@example.com', password='StrongPass123')
        Membership.objects.create(user=member, organization=self.organization, role=Membership.Role.MEMBER)
        self.client.force_authenticate(user=member)
        response = self.client.get(reverse('organization-detail', args=[self.organization.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)

        response = self.client.post(
            reverse('organization-add-member', args=[self.organization.id]),
            {'email': self.other_user.email},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)

        self.client.force_authenticate(user=self.user)
        response = self.client.get(reverse('organization-members', args=[self.organization.id]))
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertGreaterEqual(len(response.data), 2)
