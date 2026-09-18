from django.core.management.base import BaseCommand

from apps.billing.models import Plan


class Command(BaseCommand):
    help = 'Seed default plans for TeamBilling.'

    def handle(self, *args, **options):
        plans = [
            {'name': 'FREE', 'stripe_price_id': '', 'amount': 0, 'currency': 'usd', 'interval': 'month', 'active': True},
            {'name': 'PRO', 'stripe_price_id': 'price_pro_placeholder', 'amount': 29, 'currency': 'usd', 'interval': 'month', 'active': True},
            {'name': 'BUSINESS', 'stripe_price_id': 'price_business_placeholder', 'amount': 99, 'currency': 'usd', 'interval': 'month', 'active': True},
        ]

        for item in plans:
            Plan.objects.update_or_create(name=item['name'], defaults=item)

        self.stdout.write(self.style.SUCCESS('Plans seeded successfully.'))
