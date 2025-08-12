from rest_framework import viewsets, permissions
from .models import CustomUser
from .serializers import CustomUserSerializer
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework import status
from django.contrib.auth import authenticate
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.views import APIView

class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.IsAuthenticated]  # or [permissions.AllowAny] if public access
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


from rest_framework_simplejwt.tokens import RefreshToken
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken

class SingleSessionTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(username=username, password=password)
        if not user:
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        # Blacklist all existing tokens for this user
        try:
            tokens = OutstandingToken.objects.filter(user=user)
            for token in tokens:
                BlacklistedToken.objects.get_or_create(token=token)
        except Exception:
            pass

        # Create new token pair
        refresh = RefreshToken.for_user(user)
        access_jti = refresh.access_token.get("jti")
        refresh_jti = refresh.get("jti")

        # Store both JTIs
        user.last_jti = access_jti
        user.last_refresh_jti = refresh_jti
        user.save(update_fields=["last_jti", "last_refresh_jti"])

        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token)
        })

class SingleSessionTokenRefreshView(TokenRefreshView):
    def post(self, request, *args, **kwargs):
        refresh_token_str = request.data.get("refresh")
        if not refresh_token_str:
            raise AuthenticationFailed("Refresh token required.")

        try:
            refresh_token = RefreshToken(refresh_token_str)
        except Exception:
            raise AuthenticationFailed("Invalid refresh token.")

        user = self.get_user_from_token(refresh_token)

        if user.last_refresh_jti != refresh_token.get("jti"):
            raise AuthenticationFailed("Session expired. Please log in again.")

        return super().post(request, *args, **kwargs)

    def get_user_from_token(self, token):
        from django.contrib.auth import get_user_model
        User = get_user_model()
        user_id = token.get("user_id")
        return User.objects.get(id=user_id)
    

class LogoutView(APIView):
    permission_classes = [IsAuthenticated]

    def post(self, request):
        user = request.user

        # Blacklist all tokens for this user
        try:
            tokens = OutstandingToken.objects.filter(user=user)
            for token in tokens:
                BlacklistedToken.objects.get_or_create(token=token)
        except Exception:
            pass

        # Clear JTIs so even valid tokens get rejected
        user.last_jti = None
        user.last_refresh_jti = None
        user.save(update_fields=["last_jti", "last_refresh_jti"])

        return Response({"detail": "Logged out from all devices."}, status=status.HTTP_200_OK)