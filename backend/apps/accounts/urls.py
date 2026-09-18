from django.urls import path
from rest_framework_simplejwt import views as jwt_views

from .views import CustomTokenRefreshView, LoginAPIView, RegisterAPIView, UserMeAPIView

urlpatterns = [
    path('register/', RegisterAPIView.as_view(), name='register'),
    path('token/', LoginAPIView.as_view(), name='token_obtain_pair'),
    path('token/refresh/', CustomTokenRefreshView.as_view(), name='token_refresh'),
    path('me/', UserMeAPIView.as_view(), name='me'),
]
