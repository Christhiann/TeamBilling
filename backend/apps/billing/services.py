import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:
    @staticmethod
    def _is_mock_mode():
        return not settings.STRIPE_SECRET_KEY or settings.STRIPE_SECRET_KEY.startswith('sk_test_placeholder')

    @staticmethod
    def get_or_create_customer(org):
        if org.stripe_customer_id:
            return org.stripe_customer_id

        if StripeService._is_mock_mode():
            customer_id = f'cus_mock_{org.id}'
            org.stripe_customer_id = customer_id
            org.save(update_fields=['stripe_customer_id'])
            return customer_id

        owner_email = org.memberships.order_by('created_at').first().user.email if org.memberships.exists() else 'billing@teambilling.local'
        customer = stripe.Customer.create(email=owner_email)
        org.stripe_customer_id = customer.id
        org.save(update_fields=['stripe_customer_id'])
        return customer.id

    @staticmethod
    def create_checkout_session(org, plan):
        customer_id = StripeService.get_or_create_customer(org)

        if StripeService._is_mock_mode():
            class MockSession:
                url = 'https://checkout.stripe.com/mock/session'

            return MockSession()

        session = stripe.checkout.Session.create(
            customer=customer_id,
            mode='subscription',
            line_items=[{'price': plan.stripe_price_id, 'quantity': 1}],
            success_url='http://localhost:3000/billing?success=true',
            cancel_url='http://localhost:3000/billing?canceled=true',
            metadata={'organization_id': str(org.id), 'plan_id': str(plan.id)},
        )
        return session
