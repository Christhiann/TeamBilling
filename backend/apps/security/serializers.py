import pyotp
from rest_framework import serializers


class TwoFactorSetupSerializer(serializers.Serializer):
    secret = serializers.CharField(read_only=True)
    otpauth_url = serializers.CharField(read_only=True)


class TwoFactorVerifySerializer(serializers.Serializer):
    code = serializers.CharField(required=True)
