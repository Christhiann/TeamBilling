from rest_framework import serializers

from .models import Plan, Subscription


class PlanSerializer(serializers.ModelSerializer):
    class Meta:
        model = Plan
        fields = ('id', 'name', 'stripe_price_id', 'amount', 'currency', 'interval', 'active')


class SubscriptionSerializer(serializers.ModelSerializer):
    plan_name = serializers.SerializerMethodField()

    class Meta:
        model = Subscription
        fields = (
            'id',
            'organization',
            'plan',
            'plan_name',
            'stripe_customer_id',
            'stripe_subscription_id',
            'status',
            'current_period_start',
            'current_period_end',
            'cancel_at_period_end',
        )

    def get_plan_name(self, obj):
        return obj.plan.name
