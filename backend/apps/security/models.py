from django.conf import settings
from django.db import models


class TwoFactorSetup(models.Model):
    user = models.OneToOneField(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='two_factor_setup')
    secret = models.CharField(max_length=64)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'security_two_factor_setup'

    def __str__(self):
        return f'{self.user.email} setup'
