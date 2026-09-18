from django.urls import path

from .views import BillingCheckoutAPIView, BillingPlansAPIView, BillingSubscriptionAPIView, StripeWebhookAPIView

urlpatterns = [
    path('plans/', BillingPlansAPIView.as_view(), name='billing-plans'),
    path('checkout/', BillingCheckoutAPIView.as_view(), name='billing-checkout'),
    path('subscription/', BillingSubscriptionAPIView.as_view(), name='billing-subscription'),
    path('webhook/', StripeWebhookAPIView.as_view(), name='billing-webhook'),
]
