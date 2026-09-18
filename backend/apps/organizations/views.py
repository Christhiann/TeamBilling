from django.shortcuts import get_object_or_404
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView

from .models import Membership, Organization
from .serializers import MembershipSerializer, OrganizationCreateSerializer, OrganizationSerializer


class IsOrganizationMember(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if not hasattr(obj, 'memberships'):
            return False
        return obj.memberships.filter(user=request.user).exists()


class IsOrganizationOwner(permissions.BasePermission):
    def has_object_permission(self, request, view, obj):
        if not hasattr(obj, 'memberships'):
            return False
        return obj.memberships.filter(user=request.user, role=Membership.Role.OWNER).exists()


class OrganizationListCreateAPIView(generics.ListCreateAPIView):
    serializer_class = OrganizationSerializer
    permission_classes = (permissions.IsAuthenticated,)

    def get_queryset(self):
        return Organization.objects.filter(memberships__user=self.request.user).distinct()

    def get_serializer_class(self):
        if self.request.method == 'POST':
            return OrganizationCreateSerializer
        return OrganizationSerializer

    def perform_create(self, serializer):
        organization = serializer.save()
        Membership.objects.create(user=self.request.user, organization=organization, role=Membership.Role.OWNER)


class OrganizationDetailAPIView(generics.RetrieveAPIView):
    serializer_class = OrganizationSerializer
    permission_classes = (permissions.IsAuthenticated, IsOrganizationMember)

    def get_queryset(self):
        return Organization.objects.filter(memberships__user=self.request.user).distinct()


class OrganizationMembersAPIView(generics.ListAPIView):
    serializer_class = MembershipSerializer
    permission_classes = (permissions.IsAuthenticated, IsOrganizationMember)

    def get_queryset(self):
        organization = get_object_or_404(
            Organization.objects.filter(memberships__user=self.request.user),
            pk=self.kwargs['pk'],
        )
        return Membership.objects.filter(organization=organization).select_related('user')


class OrganizationMembershipsAPIView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def post(self, request, *args, **kwargs):
        organization = get_object_or_404(Organization.objects.filter(memberships__user=request.user), pk=kwargs['pk'])
        if not organization.memberships.filter(user=request.user, role=Membership.Role.OWNER).exists():
            return Response({'detail': 'Only owners can manage organization members.'}, status=status.HTTP_403_FORBIDDEN)

        email = request.data.get('email')
        if not email:
            return Response({'detail': 'Email is required.'}, status=status.HTTP_400_BAD_REQUEST)

        from django.contrib.auth import get_user_model

        User = get_user_model()
        user = User.objects.filter(email=email).first()
        if not user:
            return Response({'detail': 'User not found.'}, status=status.HTTP_404_NOT_FOUND)

        membership, created = Membership.objects.get_or_create(user=user, organization=organization)
        membership.role = Membership.Role.MEMBER
        membership.save()
        return Response({'created': created, 'membership': MembershipSerializer(membership).data}, status=status.HTTP_200_OK)
