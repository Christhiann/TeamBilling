from decimal import Decimal

from django.conf import settings
from django.db import models

from apps.organizations.models import Organization


class Plan(models.Model):
    class Interval(models.TextChoices):
        MONTHLY = 'month', 'Monthly'
        YEARLY = 'year', 'Yearly'

    name = models.CharField(max_length=50, unique=True)
    stripe_price_id = models.CharField(max_length=255, blank=True, default='')
    amount = models.DecimalField(max_digits=10, decimal_places=2, default=Decimal('0.00'))
    currency = models.CharField(max_length=3, default='usd')
    interval = models.CharField(max_length=10, choices=Interval.choices, default=Interval.MONTHLY)
    active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'billing_plan'

    def __str__(self):
        return self.name


class Subscription(models.Model):
    class Status(models.TextChoices):
        ACTIVE = 'ACTIVE', 'Active'
        CANCELED = 'CANCELED', 'Canceled'
        PAST_DUE = 'PAST_DUE', 'Past due'
        TRIALING = 'TRIALING', 'Trialing'

    organization = models.OneToOneField(Organization, on_delete=models.CASCADE, related_name='subscription')
    plan = models.ForeignKey(Plan, on_delete=models.PROTECT, related_name='subscriptions')
    stripe_customer_id = models.CharField(max_length=255, blank=True, default='')
    stripe_subscription_id = models.CharField(max_length=255, blank=True, default='')
    status = models.CharField(max_length=20, choices=Status.choices, default=Status.ACTIVE)
    current_period_start = models.DateTimeField(null=True, blank=True)
    current_period_end = models.DateTimeField(null=True, blank=True)
    cancel_at_period_end = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'billing_subscription'

    def __str__(self):
        return f'{self.organization.name} - {self.plan.name}'


class StripeEvent(models.Model):
    stripe_event_id = models.CharField(max_length=255, unique=True)
    event_type = models.CharField(max_length=255)
    processed = models.BooleanField(default=False)
    raw_data = models.JSONField()
    created_at = models.DateTimeField(auto_now_add=True)
    processed_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        db_table = 'billing_stripe_event'

    def __str__(self):
        return f'{self.event_type} ({self.stripe_event_id})'
