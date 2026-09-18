from rest_framework import serializers

from .models import Membership, Organization


class MembershipSerializer(serializers.ModelSerializer):
    user_email = serializers.SerializerMethodField()

    class Meta:
        model = Membership
        fields = ('id', 'user', 'user_email', 'role', 'created_at')

    def get_user_email(self, obj):
        return obj.user.email


class OrganizationSerializer(serializers.ModelSerializer):
    members_count = serializers.SerializerMethodField()

    class Meta:
        model = Organization
        fields = ('id', 'name', 'slug', 'stripe_customer_id', 'members_count', 'created_at')
        read_only_fields = ('id', 'stripe_customer_id', 'members_count', 'created_at')

    def get_members_count(self, obj):
        return obj.memberships.count()


class OrganizationCreateSerializer(serializers.ModelSerializer):
    class Meta:
        model = Organization
        fields = ('id', 'name', 'slug')
        read_only_fields = ('id',)
