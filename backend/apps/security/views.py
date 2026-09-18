import pyotp
from django.contrib.auth import get_user_model
from rest_framework import permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import TwoFactorSetup
from .serializers import TwoFactorSetupSerializer, TwoFactorVerifySerializer

User = get_user_model()


class TwoFactorSetupAPIView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        user = request.user
        secret = pyotp.random_base32()
        setup, _ = TwoFactorSetup.objects.get_or_create(user=user, defaults={'secret': secret})
        setup.secret = secret
        setup.save()

        otp_uri = pyotp.totp.TOTP(secret).provisioning_uri(name=user.email, issuer_name='TeamBilling')
        payload = {'secret': secret, 'otpauth_url': otp_uri}
        return Response(payload, status=status.HTTP_200_OK)


class TwoFactorVerifyAPIView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        serializer = TwoFactorVerifySerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data['code']
        setup = TwoFactorSetup.objects.filter(user=request.user).first()
        if not setup:
            return Response({'detail': '2FA setup not found.'}, status=status.HTTP_400_BAD_REQUEST)

        totp = pyotp.TOTP(setup.secret)
        if not totp.verify(code, valid_window=1):
            return Response({'detail': 'Invalid verification code.'}, status=status.HTTP_400_BAD_REQUEST)

        request.user.two_factor_enabled = True
        request.user.two_factor_secret = setup.secret
        request.user.save(update_fields=['two_factor_enabled', 'two_factor_secret'])
        return Response({'detail': '2FA enabled.'}, status=status.HTTP_200_OK)


class TwoFactorDisableAPIView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request):
        user = request.user
        setup = TwoFactorSetup.objects.filter(user=user).first()
        if setup:
            setup.delete()
        user.two_factor_enabled = False
        user.two_factor_secret = ''
        user.save(update_fields=['two_factor_enabled', 'two_factor_secret'])
        return Response({'detail': '2FA disabled.'}, status=status.HTTP_200_OK)
