from datetime import timedelta
from unittest.mock import patch

from django.contrib.auth import get_user_model
from django.utils import timezone
from django.urls import reverse
from rest_framework import status
from rest_framework.test import APITestCase

from apps.billing.models import Plan, StripeEvent, Subscription
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

    @patch('apps.billing.services.stripe.checkout.Session.create')
    def test_checkout_session_is_created_for_owner(self, session_create):
        session_create.return_value = type('Session', (), {'url': 'https://checkout.stripe.test/session_123'})()
        self.client.force_authenticate(user=self.owner)
        response = self.client.post(
            reverse('billing-checkout'),
            {'organization_id': self.organization.id, 'plan': 'PRO'},
            format='json',
        )
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertIn('checkout_url', response.data)

    @patch('apps.billing.views.stripe.Webhook.construct_event')
    def test_valid_webhook_updates_subscription(self, construct_event):
        construct_event.return_value = {
            'id': 'evt_123',
            'type': 'customer.subscription.updated',
            'data': {'object': {'id': 'sub_123', 'status': 'active', 'cancel_at_period_end': False, 'current_period_start': 1700000000, 'current_period_end': 1700003600}},
        }
        self.client.post(
            reverse('billing-webhook'),
            data=b'{}',
            format='json',
            HTTP_STRIPE_SIGNATURE='valid-signature',
        )
        self.subscription.refresh_from_db()
        self.assertEqual(self.subscription.status, Subscription.Status.ACTIVE)
        self.assertTrue(StripeEvent.objects.filter(stripe_event_id='evt_123').exists())

    @patch('apps.billing.views.stripe.Webhook.construct_event')
    def test_duplicate_webhook_is_idempotent(self, construct_event):
        construct_event.return_value = {
            'id': 'evt_duplicate',
            'type': 'customer.subscription.updated',
            'data': {'object': {'id': 'sub_123', 'status': 'active', 'cancel_at_period_end': False, 'current_period_start': 1700000000, 'current_period_end': 1700003600}},
        }
        self.client.post(reverse('billing-webhook'), b'{}', format='json', HTTP_STRIPE_SIGNATURE='valid-signature')
        response = self.client.post(reverse('billing-webhook'), b'{}', format='json', HTTP_STRIPE_SIGNATURE='valid-signature')
        self.assertEqual(response.status_code, status.HTTP_200_OK)
        self.assertEqual(StripeEvent.objects.filter(stripe_event_id='evt_duplicate').count(), 1)
