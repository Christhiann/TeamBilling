from django.urls import path

from .views import OrganizationDetailAPIView, OrganizationListCreateAPIView, OrganizationMembersAPIView, OrganizationMembershipsAPIView

urlpatterns = [
    path('', OrganizationListCreateAPIView.as_view(), name='organizations-list-create'),
    path('<int:pk>/', OrganizationDetailAPIView.as_view(), name='organization-detail'),
    path('<int:pk>/members/', OrganizationMembersAPIView.as_view(), name='organization-members'),
    path('<int:pk>/members/add/', OrganizationMembershipsAPIView.as_view(), name='organization-add-member'),
]
