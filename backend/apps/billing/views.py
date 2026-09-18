import json
from datetime import datetime

import stripe
from django.conf import settings
from django.shortcuts import get_object_or_404
from django.utils import timezone
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from apps.organizations.models import Membership, Organization

from .models import Plan, StripeEvent, Subscription
from .serializers import PlanSerializer, SubscriptionSerializer
from .services import StripeService


class IsOwnerOrReadOnly(permissions.BasePermission):
    def has_permission(self, request, view):
        if request.method in permissions.SAFE_METHODS:
            return True
        return bool(request.user and request.user.is_authenticated)

    def has_object_permission(self, request, view, obj):
        if request.method in permissions.SAFE_METHODS:
            return True
        return obj.memberships.filter(user=request.user, role=Membership.Role.OWNER).exists()


class BillingPlansAPIView(generics.ListAPIView):
    serializer_class = PlanSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Plan.objects.filter(active=True)


class BillingCheckoutAPIView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        organization_id = request.data.get('organization_id')
        plan_name = request.data.get('plan')

        if not organization_id or not plan_name:
            return Response({'detail': 'organization_id and plan are required.'}, status=status.HTTP_400_BAD_REQUEST)

        organization = get_object_or_404(
            Organization.objects.filter(memberships__user=request.user),
            pk=organization_id,
        )
        membership = organization.memberships.filter(user=request.user).first()
        if not membership or membership.role != Membership.Role.OWNER:
            return Response({'detail': 'Only organization owners can change billing.'}, status=status.HTTP_403_FORBIDDEN)

        plan = get_object_or_404(Plan, name=plan_name.upper())
        if plan.name == 'FREE':
            return Response({'detail': 'The FREE plan does not require Stripe checkout.'}, status=status.HTTP_400_BAD_REQUEST)

        session = StripeService.create_checkout_session(organization, plan)
        return Response({'checkout_url': session.url}, status=status.HTTP_200_OK)


class BillingSubscriptionAPIView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        organization_id = request.query_params.get('organization_id')
        if not organization_id:
            return Response({'detail': 'organization_id is required.'}, status=status.HTTP_400_BAD_REQUEST)

        organization = get_object_or_404(
            Organization.objects.filter(memberships__user=request.user),
            pk=organization_id,
        )
        subscription = Subscription.objects.filter(organization=organization).select_related('plan').first()
        if not subscription:
            return Response({'detail': 'No subscription found for this organization.'}, status=status.HTTP_404_NOT_FOUND)
        return Response(SubscriptionSerializer(subscription).data)


class StripeWebhookAPIView(APIView):
    permission_classes = (permissions.AllowAny,)

    def post(self, request):
        payload = request.body
        sig_header = request.META.get('HTTP_STRIPE_SIGNATURE')
        try:
            event = stripe.Webhook.construct_event(payload, sig_header, settings.STRIPE_WEBHOOK_SECRET)
        except (ValueError, stripe.error.SignatureVerificationError):
            return Response({'detail': 'Invalid Stripe signature.'}, status=status.HTTP_400_BAD_REQUEST)

        event_id = event.get('id')
        event_type = event.get('type')
        if StripeEvent.objects.filter(stripe_event_id=event_id).exists():
            return Response(status=status.HTTP_200_OK)

        stripe_event = StripeEvent.objects.create(
            stripe_event_id=event_id,
            event_type=event_type,
            processed=False,
            raw_data=event,
        )

        try:
            self._handle_event(event)
            stripe_event.processed = True
            stripe_event.processed_at = timezone.now()
            stripe_event.save(update_fields=['processed', 'processed_at'])
        except Exception:
            stripe_event.processed = False
            stripe_event.save(update_fields=['processed'])
            raise

        return Response(status=status.HTTP_200_OK)

    def _handle_event(self, event):
        event_type = event.get('type')
        data = event.get('data', {}).get('object', {})

        if event_type == 'checkout.session.completed':
            session = data
            organization_id = session.get('metadata', {}).get('organization_id')
            plan_id = session.get('metadata', {}).get('plan_id')
            if not organization_id or not plan_id:
                return
            organization = Organization.objects.get(pk=organization_id)
            plan = Plan.objects.get(pk=plan_id)
            subscription, _ = Subscription.objects.get_or_create(
                organization=organization,
                defaults={'plan': plan, 'status': Subscription.Status.ACTIVE, 'stripe_customer_id': session.get('customer')},
            )
            subscription.plan = plan
            subscription.stripe_customer_id = session.get('customer') or subscription.stripe_customer_id
            subscription.stripe_subscription_id = session.get('subscription') or subscription.stripe_subscription_id
            subscription.status = Subscription.Status.ACTIVE
            subscription.save()

        elif event_type == 'customer.subscription.updated':
            subscription_data = data
            subscription_id = subscription_data.get('id')
            if not subscription_id:
                return
            subscription = Subscription.objects.filter(stripe_subscription_id=subscription_id).select_related('plan').first()
            if subscription is None:
                return
            status_value = subscription_data.get('status', subscription.status)
            subscription.status = {
                'active': Subscription.Status.ACTIVE,
                'trialing': Subscription.Status.TRIALING,
                'past_due': Subscription.Status.PAST_DUE,
                'canceled': Subscription.Status.CANCELED,
            }.get(status_value, subscription.status)
            subscription.cancel_at_period_end = bool(subscription_data.get('cancel_at_period_end'))
            period_start = subscription_data.get('current_period_start')
            period_end = subscription_data.get('current_period_end')
            if period_start:
                subscription.current_period_start = datetime.fromtimestamp(int(period_start), tz=timezone.utc)
            if period_end:
                subscription.current_period_end = datetime.fromtimestamp(int(period_end), tz=timezone.utc)
            subscription.save()

        elif event_type == 'customer.subscription.deleted':
            subscription_data = data
            subscription_id = subscription_data.get('id')
            if not subscription_id:
                return
            subscription = Subscription.objects.filter(stripe_subscription_id=subscription_id).first()
            if subscription is None:
                return
            subscription.status = Subscription.Status.CANCELED
            subscription.cancel_at_period_end = True
            subscription.save()
