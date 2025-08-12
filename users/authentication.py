# users/authentication.py
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework.exceptions import AuthenticationFailed

class SingleSessionJWTAuthentication(JWTAuthentication):
    def get_user(self, validated_token):
        user = super().get_user(validated_token)
        token_jti = validated_token.get("jti")

        # Compare with stored JTI
        if user.last_jti != token_jti:
            raise AuthenticationFailed("Session expired. Please log in again.", code="token_invalid")
        return user
