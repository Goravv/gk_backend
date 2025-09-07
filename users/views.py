from rest_framework import viewsets, permissions
from .models import CustomUser
from .serializers import CustomUserSerializer
from rest_framework.decorators import action
from rest_framework.permissions import IsAuthenticated
from rest_framework.response import Response
from rest_framework_simplejwt.views import TokenObtainPairView
from rest_framework_simplejwt.tokens import RefreshToken
from django.contrib.auth import authenticate
from rest_framework_simplejwt.token_blacklist.models import BlacklistedToken, OutstandingToken
from rest_framework.exceptions import AuthenticationFailed
from rest_framework_simplejwt.views import TokenRefreshView
from rest_framework.views import APIView
from rest_framework import generics, status
from .serializers import RegistrationSerializer
from channels.layers import get_channel_layer
from asgiref.sync import async_to_sync

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

        # Blacklist all existing tokens for this user
        try:
            tokens = OutstandingToken.objects.filter(user=user)
            for token in tokens:
                BlacklistedToken.objects.get_or_create(token=token)

            # 🔔 Notify all active sessions via WebSocket
            channel_layer = get_channel_layer()
            async_to_sync(channel_layer.group_send)(
                f"user_{user.id}",
                {
                    "type": "logout.message",
                    "message": "You have been logged out due to a new login from another device."
                }
            )
        except Exception as e:
            print("Error blacklisting tokens or sending logout message:", e)

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
    

class RegistrationView(generics.CreateAPIView):
    queryset = CustomUser.objects.all()
    serializer_class = RegistrationSerializer

    def create(self, request, *args, **kwargs):
        serializer = self.get_serializer(data=request.data)
        if not serializer.is_valid():
            print("Validation errors:", serializer.errors)  
            return Response(serializer.errors, status=status.HTTP_400_BAD_REQUEST)
        self.perform_create(serializer)
        return Response({"message": "User registered successfully"}, status=status.HTTP_201_CREATED)



class UserPermissionView(APIView):

    def get(self, request):
        """Get all child users for the requested user"""
        parent_id = request.user.id
        users = CustomUser.objects.filter(parent_id=parent_id).values("id", "username", "permission")

        return Response(list(users), status=status.HTTP_200_OK)

    def put(self, request):
        """Update permissions for child users"""
        updates = request.data  # expecting array of {user_id, permission}

        if not isinstance(updates, list):
            return Response({"error": "Expected a list of objects"}, status=status.HTTP_400_BAD_REQUEST)

        updated_users = []

        for item in updates:
            user_id = item.get("id")
            permission = item.get("permission")

            try:
                user = CustomUser.objects.get(id=user_id, parent_id=request.user.id)
                user.permission = permission
                user.save()
                updated_users.append({"id": user.id, "username": user.username, "permission": user.permission})
            except CustomUser.DoesNotExist:
                continue  # skip invalid users

        return Response(updated_users, status=status.HTTP_200_OK)