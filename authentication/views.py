"""
Authentication APIs
"""

import logging
from datetime import datetime
from django.db import transaction
from django.contrib.auth import get_user_model
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework import permissions
from facebook_service import FacebookService
from facebook_service.models import FacebookPage, InstagramBusinessAccount
from users.models import Account, MagicLink
from facebook_service.serializers import FacebookAuthSerializer
from datetime import timedelta
from django.utils import timezone
from rest_framework_simplejwt.views import (
    TokenObtainPairView,
)
from instagram_service.models import IGUser
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
            print("token_data: ", token_data)

            if "error_type" in token_data:
                return Response(token_data, status=status.HTTP_400_BAD_REQUEST)

            long_lived_token_data = InstagramService.get_long_lived_token(
                token_data["access_token"]
            )
            if "error_type" in long_lived_token_data:
                return Response(
                    long_lived_token_data, status=status.HTTP_400_BAD_REQUEST
                )
            print("long_lived_token_data", long_lived_token_data)

            profile_data = InstagramService.get_user_profile(
                long_lived_token_data["access_token"]
            )
            print("profile_data", profile_data)

            if "error" in profile_data:
                return Response(
                    profile_data, status=status.HTTP_400_BAD_REQUEST
                )

            username = profile_data.get("username")

            # Create or get user with this social account
            account = Account.objects.filter(
                provider="instagram", provider_account_id=token_data["user_id"]
            ).first()
            print("account", account)

            if account:
                # Existing user
                print("user: ")
                user = account.user
                print("user: ", user)
                # Update token and user_type
                account.access_token = long_lived_token_data["access_token"]
                account.updated_at = timezone.now()
                print("updated_at", account.updated_at)
                account.save()
            else:
                # Create new user and account
                user_data = {
                    "username": username,
                    "name": username,
                    "email": f"{username}@influenceai.com",
                    "user_type": user_type,
                }
                print("user_data", user_data)

                # Check if user with this email exists
                try:
                    user = User.objects.get(username=username)
                except User.DoesNotExist:
                    user = User.objects.create_user(**user_data)
                # Create account
                print("user", user)
                account = Account.objects.create(
                    user=user,
                    type="oauth",
                    provider="instagram",
                    provider_account_id=token_data["user_id"],
                    access_token=long_lived_token_data["access_token"],
                )
            print("calling... ig_data")
            ig_data = InstagramService.get_instagram_user_profile(
                access_token=account.access_token,
                instagram_id=account.provider_account_id,
            )
            print("ig_data", ig_data)
            if "error" in ig_data:
                return Response(ig_data, status=status.HTTP_400_BAD_REQUEST)
            # Save IG data
            ig_data["user_scope_id"] = ig_data.get("id")
            ig_data.pop("id")
            ig_user = IGUser.objects.update_or_create(
                account=account,
                defaults=ig_data,
            )
            print("IG User frs: ", ig_user.followers_count)
            # Generate JWT token
            user_serializer = SocialAuthUserSerializer(user)
            data = user_serializer.data
            return Response(data)

        except Exception as e:
            return Response(
                {"error": str(e)}, status=status.HTTP_400_BAD_REQUEST
            )


class FacebookTokenAuthView(APIView):
    """
    Handle Facebook token authentication and account creation
    """

    permission_classes = [permissions.AllowAny]

    @transaction.atomic
    def post(self, request):
        """
        Authenticate with Facebook token, create user if needed,
        and return JWT token
        """
        serializer = FacebookAuthSerializer(data=request.data)
        if not serializer.is_valid():
            return Response(
                {
                    "message": "Invalid request data",
                    "errors": serializer.errors,
                },
                status=status.HTTP_400_BAD_REQUEST,
            )

        # Extract access token from validated data
        access_token = serializer.validated_data.get("access_token")

        try:
            # Step 1: Verify the token and get user data
            token_verification = FacebookService.debug_token(access_token)
            print("Verifying access token", token_verification)
            if token_verification.get("error") or token_verification.get(
                "data"
            ).get("is_valid)"):
                return Response(
                    {"message": "Token Expired, please login again"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )

            # Step 2: Exchange for long-lived token
            token_exchange = FacebookService.exchange_for_long_lived_token(
                access_token
            )
            if not token_exchange["success"]:
                return Response(
                    {"message": "Failed to exchange token"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            print("longlivedtoken: ", token_exchange)
            long_lived_token = token_exchange["access_token"]

            # Step 3: Get connected Instagram accounts
            connected_accounts = FacebookService.get_connected_accounts(
                long_lived_token
            )
            print("coennected accounts: ", connected_accounts)
            if not connected_accounts["success"]:
                return Response(
                    {"message": "Failed to get connected accounts"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )
            page_id = connected_accounts["data"]["data"][0]["id"]
            print("page_id: ", page_id)

            ig_account = FacebookService.get_ig_business_account(
                page_id, long_lived_token
            )
            print("ig_account: ", ig_account)
            if not ig_account["success"]:
                return Response(
                    {"message": "Failed to get Instagram Business account"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            pages_with_instagram = connected_accounts["data"]["pages"]
            if not pages_with_instagram:
                return Response(
                    {
                        "message": "No Instagram Business account found.\
                              Please connect an Instagram Business account\
                            to your Facebook Page."
                    },
                    status=status.HTTP_400_BAD_REQUEST,
                )
            fb_data = FacebookService.verify_me(access_token)
            print("fb_data: ", fb_data)
            if not fb_data["success"]:
                return Response(
                    {"message": "Invalid Facebook token"},
                    status=status.HTTP_401_UNAUTHORIZED,
                )
            fb_user_data = fb_data["data"]
            ig_data = FacebookService.get_instagram_user_profile(
                page_id, long_lived_token
            )
            print("ig_data: ", ig_data)

            # Step 4: Get or create user
            user, account = self._get_or_create_user_and_account(
                fb_user_data, long_lived_token, "brand", "facebook"
            )

            # Step 5: Save Facebook pages and Instagram accounts
            # saved_instagram_accounts = []
            # for page in pages_with_instagram:
            #     saved_account = self._save_page_and_instagram(
            #         account=account,
            #         page_data=page,
            #     )
            #     if saved_account:
            #         saved_instagram_accounts.append(saved_account)

            # Step 6: Generate JWT token
            serializer = SocialAuthUserSerializer(user)
            auth_data = serializer.data
            return Response(auth_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception(
                "Error during Facebook authentication: %s", str(e)
            )
            return Response(
                {"message": f"Authentication failed: {str(e)}"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )

    def _get_or_create_user_and_account(
        self, fb_data, longlivedtoken, user_type, provider
    ):
        """
        Get or create user and associated account based on Facebook data
        """
        fb_id = fb_data.get("id")
        email = fb_data.get("email")

        # If email is not provided, create one based on FB ID
        if not email:
            email = f"{fb_id}@facebook.com"

        # Try to find existing account by provider and provider_account_id
        existing_account = Account.objects.filter(
            provider=provider, provider_account_id=fb_id
        ).first()

        if existing_account:
            existing_account.access_token = longlivedtoken
            return existing_account.user, existing_account

        # Try to find user by email
        try:
            user = User.objects.get(email=email)
        except User.DoesNotExist:
            # Create new user
            user = User.objects.create_user(
                username=f"fb_{fb_id}",
                email=email,
                password=User.objects.make_random_password(),
                name=f"{fb_data.get('first_name', '')} \
                    {fb_data.get('last_name', '')}".strip(),
                user_type=user_type,
            )

        # Create account for this user
        account = Account.objects.create(
            user=user,
            type="oauth",
            provider=provider,
            provider_account_id=fb_id,
            access_token=longlivedtoken,
            description=f"Facebook account for {user.email}",
        )

        return user, account

    def _save_page_and_instagram(self, account, page_data, token_expires_at):
        """
        Save Facebook Page and connected Instagram account
        """
        if not page_data.get("instagram_business_account"):
            return None

        # Get or create Facebook Page
        page, created = FacebookPage.objects.update_or_create(
            page_id=page_data.get("id"),
            defaults={
                "account": account,
                "name": page_data.get("name", "Facebook Page"),
            },
        )

        # Get Instagram account data
        ig_data = page_data.get("instagram_business_account", {})
        ig_id = ig_data.get("id")

        if not ig_id:
            return None

        # Get more details about Instagram account
        ig_details = FacebookService.get_instagram_user_profile(
            ig_id, page.access_token
        )

        if not ig_details["success"]:
            logger.error(f"Failed to get Instagram details for {ig_id}")
            ig_details_data = ig_data
        else:
            ig_details_data = ig_details["data"]

        # Create or update Instagram account
        instagram_account, created = (
            InstagramBusinessAccount.objects.update_or_create(
                instagram_id=ig_id,
                defaults={
                    "facebook_page": page,
                    "username": ig_details_data.get("username", ""),
                    "name": ig_details_data.get("name", ""),
                    "profile_picture_url": ig_details_data.get(
                        "profile_picture_url"
                    ),
                    "biography": ig_details_data.get("biography", ""),
                    "website": ig_details_data.get("website", ""),
                    "follows_count": ig_details_data.get("follows_count", 0),
                    "followers_count": ig_details_data.get(
                        "followers_count", 0
                    ),
                    "media_count": ig_details_data.get("media_count", 0),
                    "is_verified": ig_details_data.get("is_verified", False),
                },
            )
        )

        return instagram_account
