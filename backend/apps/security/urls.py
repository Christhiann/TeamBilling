from django.urls import path

from .views import TwoFactorDisableAPIView, TwoFactorSetupAPIView, TwoFactorVerifyAPIView

urlpatterns = [
    path('2fa/setup/', TwoFactorSetupAPIView.as_view(), name='twofactor-setup'),
    path('2fa/verify/', TwoFactorVerifyAPIView.as_view(), name='twofactor-verify'),
    path('2fa/disable/', TwoFactorDisableAPIView.as_view(), name='twofactor-disable'),
]
