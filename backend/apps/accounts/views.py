from django.contrib.auth import get_user_model
from rest_framework import generics, permissions, status
from rest_framework.response import Response
from rest_framework.views import APIView
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from .serializers import CustomTokenObtainPairSerializer, RegisterSerializer, UserSerializer

User = get_user_model()


class RegisterAPIView(generics.CreateAPIView):
    queryset = User.objects.all()
    permission_classes = (permissions.AllowAny,)
    serializer_class = RegisterSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        serializer.is_valid(raise_exception=True)
        user = serializer.save()
        refresh = self.get_tokens_for_user(user)
        response_data = {
            'token': {
                'refresh': str(refresh),
                'access': str(refresh.access_token),
            },
            'user': UserSerializer(user).data,
        }
        return Response(response_data, status=status.HTTP_201_CREATED)

    def get_tokens_for_user(self, user):
        from rest_framework_simplejwt.tokens import RefreshToken

        refresh = RefreshToken.for_user(user)
        return refresh


class LoginAPIView(TokenObtainPairView):
    serializer_class = CustomTokenObtainPairSerializer


class UserMeAPIView(APIView):
    permission_classes = (permissions.IsAuthenticated,)

    def get(self, request):
        serializer = UserSerializer(request.user)
        return Response(serializer.data)


class CustomTokenRefreshView(TokenRefreshView):
    pass
