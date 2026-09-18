from datetime import timedelta

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.billing.models import Plan, Subscription
from apps.organizations.models import Membership, Organization

User = get_user_model()


class BillingAPITests(APITestCase):
    def setUp(self):
        self.owner = User.objects.create_user(email='owner2@example.com', password='StrongPass123')
        self.member = User.objects.create_user(email='member2@example.com', password='StrongPass123')
        self.organization = Organization.objects.create(name='Billing Org', slug='billing-org')
        Membership.objects.create(user=self.owner, organization=self.organization, role=Membership.Role.OWNER)
        Membership.objects.create(user=self.member, organization=self.organization, role=Membership.Role.MEMBER)
        self.plan = Plan.objects.create(name='PRO', stripe_price_id='price_123', amount=29, currency='usd', interval='month')
        self.subscription = Subscription.objects.create(
            organization=self.organization,
            plan=self.plan,
            stripe_customer_id='cus_123',
            stripe_subscription_id='sub_123',
            status=Subscription.Status.ACTIVE,
            current_period_start=timezone.now(),
            current_period_end=timezone.now() + timedelta(days=30),
        )

    def test_owner_can_access_billing_subscription(self):
        self.client.force_authenticate(user=self.owner)
        response = self.client.get(reverse('billing-subscription'), {'organization_id': self.organization.id})
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(response.data['plan_name'], 'PRO')

    def test_member_cannot_change_billing(self):
        self.client.force_authenticate(user=self.member)
        response = self.client.post(
            reverse('billing-checkout'),
            {'organization_id': self.organization.id, 'plan': 'PRO'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_403_FORBIDDEN)
