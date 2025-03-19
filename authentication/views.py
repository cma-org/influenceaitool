"""
Authentication APIs
"""

from datetime import timedelta
import logging
import requests
from django.conf import settings
from django.contrib.auth import get_user_model
from django.utils import timezone
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions, status
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
)
from users.models import Account, MagicLink
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
        print("email_sent: ", email_sent)
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
            print("user: ", user)
            magic_link = MagicLink.objects.get(
                user=user,
                token=token,
                is_used=False,
                expires_at__gt=timezone.now(),
            )
            print("magic_link: ", magic_link)

            # Mark as used
            magic_link.is_used = True
            magic_link.save()

            # Generate JWT
            user_serializer = MagicLinkAuthUserSerializer(user)
            data = user_serializer.data
            print("data: ", data)

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


class InstagramLoginView(APIView):
    """
    Generate Instagram OAuth URL for influencers
    """

    permission_classes = [permissions.AllowAny]

    def get(self, request):
        # Instagram OAuth URL
        cid = settings.INSTAGRAM_CLIENT_ID
        redirect_uri = settings.INSTAGRAM_REDIRECT_URI
        host = "https://www.instagram.com/oauth/authorize"

        # Build URL with parameters
        auth_url = (
            f"{host}?enable_fb_login=0&force_authentication=1&client_id={cid}"
            f"&redirect_uri={redirect_uri}&response_type=code&scope="
            f"instagram_business_basic%2Cinstagram_business_manage_messages%2C"
            f"instagram_business_manage_comments%2C"
            f"instagram_business_content_publish%2C"
            f"instagram_business_manage_insights"
        )
        return Response({"login_url": auth_url})


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
        print("code", code, user_type)

        try:
            # Exchange code for access token
            token_url = "https://api.instagram.com/oauth/access_token"
            print("redirect_uri", settings.INSTAGRAM_REDIRECT_URI)

            token_payload = {
                "client_id": settings.INSTAGRAM_CLIENT_ID,
                "client_secret": settings.INSTAGRAM_CLIENT_SECRET,
                "grant_type": "authorization_code",
                "redirect_uri": settings.INSTAGRAM_REDIRECT_URI,
                "code": code,
            }

            token_response = requests.post(token_url, data=token_payload)
            token_data = token_response.json()
            print("token_response", token_data)

            if "error_type" in token_data:
                return Response(token_data, status=status.HTTP_400_BAD_REQUEST)

            ast = token_data["access_token"]
            user_id = token_data["user_id"]
            host = "https://graph.instagram.com/access_token"
            cst = settings.INSTAGRAM_CLIENT_SECRET

            # get long lived token
            long_lived_token_url = (
                f"{host}?grant_type=ig_exchange_token&"
                f"client_secret={cst}&access_token={ast}"
            )

            long_lived_token_response = requests.get(
                long_lived_token_url,
                timeout=1000,
            )
            long_lived_token_data = long_lived_token_response.json()
            print("long_lived_token_response", long_lived_token_data)

            if "error_type" in long_lived_token_data:
                return Response(
                    long_lived_token_data, status=status.HTTP_400_BAD_REQUEST
                )

            llast = long_lived_token_data["access_token"]

            # Get user profile data
            HOST = "https://graph.instagram.com"
            profile_url = f"{HOST}/me?fields=id,username&access_token={llast}"
            profile_response = requests.get(profile_url)
            profile_data = profile_response.json()
            print("profile_data", profile_data)

            if "error" in profile_data:
                return Response(
                    profile_data, status=status.HTTP_400_BAD_REQUEST
                )

            username = profile_data.get("username")

            # Create or get user with this social account
            account = Account.objects.filter(
                provider="instagram", provider_account_id=user_id
            ).first()
            print("account", account)

            if account:
                # Existing user
                user = account.user
                # Update token and user_type
                account.access_token = llast
                account.user_type = user_type  # Update user_type
                account.updated_at = timezone.now()
                account.save()
            else:
                # Create new user and account
                user_data = {
                    "username": username,
                    "name": username,
                    "email": "user@influenceai.com",
                }

                # Check if user with this email exists
                try:
                    print("get user")
                    user = User.objects.get(username=username)
                except User.DoesNotExist:
                    print("create user")
                    user = User.objects.create_user(**user_data)
                print(user)
                # Create account
                acc = Account.objects.create(
                    user=user,
                    type="oauth",
                    provider="instagram",
                    provider_account_id=user_id,
                    access_token=llast,
                    user_type=user_type,  # Store user_type
                )
                print("acc:", acc)

            # Generate JWT token
            user_serializer = SocialAuthUserSerializer(user)
            data = user_serializer.data
            print("data: ", data)
            return Response(data)

        except Exception as e:
            print("error:", e)
            return Response(
                {"error": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )
