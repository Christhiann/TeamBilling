from django.conf import settings
from django.db import models


class Organization(models.Model):
    name = models.CharField(max_length=150)
    slug = models.SlugField(max_length=120, unique=True)
    stripe_customer_id = models.CharField(max_length=255, blank=True, default='')
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = 'organizations_organization'

    def __str__(self):
        return self.name


class Membership(models.Model):
    class Role(models.TextChoices):
        OWNER = 'OWNER', 'Owner'
        MEMBER = 'MEMBER', 'Member'

    user = models.ForeignKey(settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name='memberships')
    organization = models.ForeignKey(Organization, on_delete=models.CASCADE, related_name='memberships')
    role = models.CharField(max_length=20, choices=Role.choices, default=Role.MEMBER)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'organizations_membership'
        unique_together = ('user', 'organization')

    def __str__(self):
        return f'{self.user.email} -> {self.organization.name} ({self.role})'
