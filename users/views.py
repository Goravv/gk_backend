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

class CustomUserViewSet(viewsets.ModelViewSet):
    queryset = CustomUser.objects.all()
    serializer_class = CustomUserSerializer
    permission_classes = [permissions.IsAuthenticated]  # or [permissions.AllowAny] if public access
    @action(detail=False, methods=['get'], permission_classes=[IsAuthenticated])
    def me(self, request):
        serializer = self.get_serializer(request.user)
        return Response(serializer.data)


class SingleSessionTokenObtainPairView(TokenObtainPairView):
    def post(self, request, *args, **kwargs):
        username = request.data.get("username")
        password = request.data.get("password")

        user = authenticate(username=username, password=password)
        if not user:
            return Response({"detail": "Invalid credentials"}, status=status.HTTP_401_UNAUTHORIZED)

        # Blacklist old token if exists
        if user.last_refresh_token:
            try:
                old_token = RefreshToken(user.last_refresh_token)
                old_token.blacklist()
            except Exception:
                pass

        # Create new tokens
        refresh = RefreshToken.for_user(user)

        # Store the new refresh token in DB
        user.last_refresh_token = str(refresh)
        user.save(update_fields=["last_refresh_token"])

        return Response({
            "refresh": str(refresh),
            "access": str(refresh.access_token)
        })