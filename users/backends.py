"""
AUthentication Backend
"""

from django.contrib.auth import get_user_model
from rest_framework_simplejwt.authentication import JWTAuthentication
from rest_framework_simplejwt.exceptions import InvalidToken, TokenError
from rest_framework import status
from rest_framework.response import Response


User = get_user_model()


class JWTSocialAuthentication(JWTAuthentication):
    """
    Custom JWT authentication that also extracts the provider information
    from the token payload.
    """

    def authenticate(self, request):
        auth_header = request.META.get("HTTP_AUTHORIZATION", "")
        print(
            "Auth header:",
            request.META.get("HTTP_AUTHORIZATION", "No auth header"),
        )
        if not auth_header:
            return None

        try:
            auth_type, token = auth_header.split()
            if auth_type.lower() != "bearer":
                return None

            print("User:", request.user)
            print("Auth info:", getattr(request, "auth", None))

            # Standard JWT authentication
            auth_result = super().authenticate(request)

            if auth_result is None:
                return None

            user, token = auth_result

            # Extract provider info from token if available
            provider = token.get("provider", None)
            user_type = token.get("user_type", None)

            # Return user and provider/type info for the view to use
            return (
                user,
                {"token": token, "provider": provider, "user_type": user_type},
            )

        except (InvalidToken, TokenError, ValueError) as e:
            return Response(
                {
                    "detail": "Authentication Failed",
                    "error": str(e),
                },
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
