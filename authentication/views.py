"""
Authentication APIs
"""

from datetime import timedelta
import logging
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
)
from users.models import Account, MagicLink
from instagram_service import InstagramService
from .serializers import (
    CustomTokenObtainPairSerializer,
    SocialLoginSerializer,
    MagicLinkAuthUserSerializer,
    SocialAuthUserSerializer,
)
from .utils import generate_token
from .email_service import EmailService

User = get_user_model()

# Set up logger
logger = logging.getLogger(__name__)

User = get_user_model()


class GenerateMagicLinkView(APIView):
    """Generate Token view"""

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        email = request.data.get("email")
        user_type = request.data.get("user_type", "Influencer")

        if not email:
            return Response(
                {"error": "Email is required"},
                status=status.HTTP_400_BAD_REQUEST,
            )
        # Check if user exists first
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Create new user with email as username
            username = email.split("@")[0]
            user = User.objects.create(email=email, username=username)
            # Set user type or any other fields
            if hasattr(user, "user_type"):
                user.user_type = user_type
                user.save()

        # Generate UUID token
        token = generate_token()

        # Set expiration (24 hours) using timezone-aware datetime
        expiry = timezone.now() + timedelta(hours=24)

        # Store in database
        magic_link = MagicLink.objects.create(
            user=user, token=token, expires_at=expiry
        )

        # Send email with magic link
        email_sent = EmailService.send_magic_link(email, str(token), user_type)
        if email_sent.get("status") != 200:
            magic_link.delete()
            return Response(
                email_sent,
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

        return Response(
            {
                "success": True,
                "message": "Magic link sent to your email",
                "expires_at": expiry,
            },
            status=status.HTTP_200_OK,
        )


class VerifyMagicLinkView(APIView):
    """
    Verify Token View
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        token = request.data.get("token")
        email = request.data.get("email")

        if not token or not email:
            return Response(
                {"error": "Invalid request"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        try:
            user = User.objects.get(email=email)
            magic_link = MagicLink.objects.get(
                user=user,
                token=token,
                is_used=False,
                expires_at__gt=timezone.now(),
            )

            # Mark as used
            magic_link.is_used = True
            magic_link.save()

            # Generate JWT
            user_serializer = MagicLinkAuthUserSerializer(user)
            data = user_serializer.data

            return Response(data, status=status.HTTP_201_CREATED)

        except (User.DoesNotExist, MagicLink.DoesNotExist):
            return Response(
                {"error": "Invalid or expired token"},
                status=status.HTTP_401_UNAUTHORIZED,
            )


class CustomTokenObtainPairView(TokenObtainPairView):
    """
    Custom token view that uses our serializer class
    """

    serializer_class = CustomTokenObtainPairSerializer


class InstagramAuthCallbackView(APIView):
    """
    Handle Instagram OAuth callback for influencers
    """

    permission_classes = [permissions.AllowAny]

    def post(self, request):
        serializer = SocialLoginSerializer(data=request.data)
        serializer.is_valid(raise_exception=True)

        code = serializer.validated_data["code"]
        user_type = serializer.validated_data.get("user_type", "influencer")

        try:
            # Exchange code for access token

            token_data = InstagramService.get_access_token(code)

            if "error_type" in token_data:
                return Response(token_data, status=status.HTTP_400_BAD_REQUEST)

            long_lived_token_data = InstagramService.get_long_lived_token(
                token_data["access_token"]
            )
            if "error_type" in long_lived_token_data:
                return Response(
                    long_lived_token_data, status=status.HTTP_400_BAD_REQUEST
                )

            profile_data = InstagramService.get_user_profile(
                long_lived_token_data["access_token"]
            )

            if "error" in profile_data:
                return Response(
                    profile_data, status=status.HTTP_400_BAD_REQUEST
                )

            username = profile_data.get("username")

            # Create or get user with this social account
            account = Account.objects.filter(
                provider="instagram", provider_account_id=token_data["user_id"]
            ).first()

            if account:
                # Existing user
                user = account.user
                # Update token and user_type
                account.access_token = long_lived_token_data["access_token"]
                account.user_type = user_type  # Update user_type
                account.updated_at = timezone.now()
                account.save()
            else:
                # Create new user and account
                user_data = {
                    "username": username,
                    "name": username,
                    "email": f"{username}@influenceai.com",
                    "user_type": user_type,
                }

                # Check if user with this email exists
                try:
                    user = User.objects.get(username=username)
                except User.DoesNotExist:
                    user = User.objects.create_user(**user_data)
                # Create account
                Account.objects.create(
                    user=user,
                    type="oauth",
                    provider="instagram",
                    provider_account_id=token_data["user_id"],
                    access_token=long_lived_token_data["access_token"],
                )

            # Generate JWT token
            user_serializer = SocialAuthUserSerializer(user)
            data = user_serializer.data
            return Response(data)

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )
