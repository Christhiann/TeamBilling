import stripe
from django.conf import settings

stripe.api_key = settings.STRIPE_SECRET_KEY


class StripeService:
    @staticmethod
    def get_or_create_customer(org):
        if org.stripe_customer_id:
            return org.stripe_customer_id

        customer = stripe.Customer.create(email=org.name)
        org.stripe_customer_id = customer.id
        org.save(update_fields=['stripe_customer_id'])
        return customer.id

    @staticmethod
    def create_checkout_session(org, plan):
        customer_id = StripeService.get_or_create_customer(org)
        session = stripe.checkout.Session.create(
            customer=customer_id,
            mode='subscription',
            line_items=[{'price': plan.stripe_price_id, 'quantity': 1}],
            success_url='http://localhost:3000/billing?success=true',
            cancel_url='http://localhost:3000/billing?canceled=true',
            metadata={'organization_id': str(org.id), 'plan_id': str(plan.id)},
        )
        return session
