"""
API for user media
"""

import logging
from rest_framework import status
from rest_framework.views import APIView
from rest_framework.response import Response
from rest_framework.permissions import IsAuthenticated
from users.models import Account
from .instagram_service import InstagramService

logger = logging.getLogger(__name__)


class InstagramMediaView(APIView):
    """
    API view to fetch Instagram media for the authenticated user
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        """Get user from the request"""

        user = request.user

        # Attempt to get provider info from the authentication
        auth_info = getattr(request, "auth", None)
        provider = None

        if isinstance(auth_info, dict) and "provider" in auth_info:
            provider = auth_info.get("provider")

        # Determine which provider to use based on available info
        if provider == "instagram":
            account_filter = {"provider": "instagram"}
        elif provider == "facebook" or provider == "instagram_business":
            account_filter = {
                "provider__in": ["instagram_business", "facebook"]
            }
        else:
            # If no specific provider in token,
            # try instagram first, then facebook
            account_filter = {
                "provider__in": ["instagram", "instagram_business", "facebook"]
            }

        # Get the appropriate account for the user
        account = (
            Account.objects.filter(user=user, **account_filter)
            .order_by("-updated_at")
            .first()
        )

        if not account:
            return Response(
                {"error": "No Instagram account found for this user"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Determine the correct ID to use
        if account.provider == "instagram":
            ig_id = account.provider_account_id
        elif account.provider == "instagram_business":
            ig_id = account.provider_account_id
        else:  # Facebook account
            # For Facebook, we don't have direct
            # Instagram ID in our current implementation
            # This would need to be enhanced to properly
            # fetch linked Instagram accounts
            return Response(
                {"error": "Instagram business account details not available"},
                status=status.HTTP_400_BAD_REQUEST,
            )

        # # Get limit from query params, default to 25
        # limit = request.query_params.get("limit", 25)
        # try:
        #     limit = int(limit)
        # except ValueError:
        #     limit = 25

        # Get the user's media from Instagram
        media_data = InstagramService.get_user_media(
            ig_id=ig_id, access_token=account.access_token
        )

        # Check if there was an error
        if "error" in media_data:
            return Response(media_data, status=status.HTTP_400_BAD_REQUEST)

        return Response(media_data)


class InstagramMediaDetailView(APIView):
    """
    API view to fetch details for a specific Instagram media
    """

    permission_classes = [IsAuthenticated]

    def get(self, request, media_id):
        # Get user and account similar to InstagramMediaView
        user = request.user
        account = (
            Account.objects.filter(
                user=user, provider__in=["instagram", "instagram_business"]
            )
            .order_by("-updated_at")
            .first()
        )

        if not account:
            return Response(
                {"error": "No Instagram account found for this user"},
                status=status.HTTP_404_NOT_FOUND,
            )

        # Get details for the specific media
        media_details = InstagramService.get_media_details(
            media_id=media_id, access_token=account.access_token
        )

        if "error" in media_details:
            return Response(media_details, status=status.HTTP_400_BAD_REQUEST)

        return Response(media_details)


class InstagramAccountInsightsView(APIView):
    """
    View to get basic account insights from Instagram
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user

            # Attempt to get provider info from the authentication
            auth_info = getattr(request, "auth", None)
            provider = None

            if isinstance(auth_info, dict) and "provider" in auth_info:
                provider = auth_info.get("provider")

            # Determine which provider to use based on available info
            if provider == "instagram":
                account_filter = {"provider": "instagram"}
            elif provider == "facebook" or provider == "instagram_business":
                account_filter = {
                    "provider__in": ["instagram_business", "facebook"]
                }
            else:
                # If no specific provider in token,
                # try instagram first, then facebook
                account_filter = {
                    "provider__in": [
                        "instagram",
                        "instagram_business",
                        "facebook",
                    ]
                }

            # Get the appropriate account for the user
            account = (
                Account.objects.filter(user=user, **account_filter)
                .order_by("-updated_at")
                .first()
            )

            if not account:
                return Response(
                    {"error": "No Instagram account found for this user"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Determine the correct ID to use
            if account.provider == "instagram":
                instagram_id = account.provider_account_id
            elif account.provider == "instagram_business":
                instagram_id = account.provider_account_id
            else:
                return Response(
                    {"error": "Instagram business account not available"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            access_token = account.access_token

            if not instagram_id or not access_token:
                return Response(
                    {"error": "Instagram account not connected"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            insights = InstagramService.get_account_basic_insights(
                instagram_id, access_token
            )

            if "error" in insights:
                logger.error(
                    "Error fetching Instagram account insights:%s",
                    {insights["error"]},
                )
                return Response(
                    {"error": "Failed to fetch account insights"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            return Response(insights, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception(
                "Unexpected error in InstagramAccountInsightsView %s", e
            )
            return Response(
                {"error": "An unexpected error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class InstagramFollowersGrowthView(APIView):
    """
    View to get followers growth data from Instagram
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user

            # Attempt to get provider info from the authentication
            auth_info = getattr(request, "auth", None)
            provider = None

            if isinstance(auth_info, dict) and "provider" in auth_info:
                provider = auth_info.get("provider")

            # Determine which provider to use based on available info
            if provider == "instagram":
                account_filter = {"provider": "instagram"}
            elif provider == "facebook" or provider == "instagram_business":
                account_filter = {
                    "provider__in": ["instagram_business", "facebook"]
                }
            else:
                # If no specific provider in token, try instagram first,
                #  then facebook
                account_filter = {
                    "provider__in": [
                        "instagram",
                        "instagram_business",
                        "facebook",
                    ]
                }

            # Get the appropriate account for the user
            account = (
                Account.objects.filter(user=user, **account_filter)
                .order_by("-updated_at")
                .first()
            )

            if not account:
                return Response(
                    {"error": "No Instagram account found for this user"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Determine the correct ID to use
            if account.provider == "instagram":
                instagram_id = account.provider_account_id
            elif account.provider == "instagram_business":
                instagram_id = account.provider_account_id
            else:
                return Response(
                    {"error": "Instagram business account not available"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            access_token = account.access_token
            days = request.query_params.get("days", 30)

            try:
                days = int(days)
            except ValueError:
                days = 30

            if not instagram_id or not access_token:
                return Response(
                    {"error": "Instagram account not connected"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            growth_data = InstagramService.get_followers_growth(
                instagram_id, access_token, days
            )

            if "error" in growth_data:
                logger.error(
                    f"Error fetching followers growth: {growth_data['error']}"
                )
                return Response(
                    {"error": "Failed to fetch followers growth data"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            return Response(growth_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception(
                "Unexpected error in InstagramFollowersGrowthView", str(e)
            )
            return Response(
                {"error": "An unexpected error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class InstagramPostEngagementsView(APIView):
    """
    View to get post engagements data from Instagram
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user

            # Attempt to get provider info from the authentication
            auth_info = getattr(request, "auth", None)
            provider = None

            if isinstance(auth_info, dict) and "provider" in auth_info:
                provider = auth_info.get("provider")

            # Determine which provider to use based on available info
            if provider == "instagram":
                account_filter = {"provider": "instagram"}
            elif provider == "facebook" or provider == "instagram_business":
                account_filter = {
                    "provider__in": ["instagram_business", "facebook"]
                }
            else:
                # If no specific provider in token, try instagram first,
                #  then facebook
                account_filter = {
                    "provider__in": [
                        "instagram",
                        "instagram_business",
                        "facebook",
                    ]
                }

            # Get the appropriate account for the user
            account = (
                Account.objects.filter(user=user, **account_filter)
                .order_by("-updated_at")
                .first()
            )

            if not account:
                return Response(
                    {"error": "No Instagram account found for this user"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Determine the correct ID to use
            if account.provider == "instagram":
                instagram_id = account.provider_account_id
            elif account.provider == "instagram_business":
                instagram_id = account.provider_account_id
            else:
                return Response(
                    {"error": "Instagram business account not available"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            access_token = account.access_token
            months = request.query_params.get("months", 6)

            try:
                months = int(months)
            except ValueError:
                months = 6

            if not instagram_id or not access_token:
                return Response(
                    {"error": "Instagram account not connected"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            engagement_data = InstagramService.get_post_engagements(
                instagram_id, access_token, months
            )

            if "error" in engagement_data:

                return Response(
                    {"error": "Failed to fetch post engagements data"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            return Response(engagement_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception(
                "Unexpected error in InstagramPostEngagementsView", str(e)
            )
            return Response(
                {"error": "An unexpected error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class InstagramCurrentMonthLikesView(APIView):
    """
    View to get current month likes data from Instagram
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user

            # Attempt to get provider info from the authentication
            auth_info = getattr(request, "auth", None)
            provider = None

            if isinstance(auth_info, dict) and "provider" in auth_info:
                provider = auth_info.get("provider")

            # Determine which provider to use based on available info
            if provider == "instagram":
                account_filter = {"provider": "instagram"}
            elif provider == "facebook" or provider == "instagram_business":
                account_filter = {
                    "provider__in": ["instagram_business", "facebook"]
                }
            else:
                # If no specific provider in token, try instagram first,
                #  then facebook
                account_filter = {
                    "provider__in": [
                        "instagram",
                        "instagram_business",
                        "facebook",
                    ]
                }

            # Get the appropriate account for the user
            account = (
                Account.objects.filter(user=user, **account_filter)
                .order_by("-updated_at")
                .first()
            )

            if not account:
                return Response(
                    {"error": "No Instagram account found for this user"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Determine the correct ID to use
            if account.provider == "instagram":
                instagram_id = account.provider_account_id
            elif account.provider == "instagram_business":
                instagram_id = account.provider_account_id
            else:
                return Response(
                    {"error": "Instagram business account  not available"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            access_token = account.access_token

            if not instagram_id or not access_token:
                return Response(
                    {"error": "Instagram account not connected"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            likes_data = InstagramService.get_current_month_likes(
                instagram_id, access_token
            )

            if "error" in likes_data:
                logger.error(
                    f"err  Insta current month likes: {likes_data['error']}"
                )
                return Response(
                    {"error": "Failed to fetch current month likes data"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            return Response(likes_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception(
                "Unexpected error in InstagramCurrentMonthLikesView", str(e)
            )
            return Response(
                {"error": "An unexpected error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )


class InstagramDemographicsView(APIView):
    """
    View to get demographic insights from Instagram
    """

    permission_classes = [IsAuthenticated]

    def get(self, request):
        try:
            user = request.user

            # Attempt to get provider info from the authentication
            auth_info = getattr(request, "auth", None)
            provider = None

            if isinstance(auth_info, dict) and "provider" in auth_info:
                provider = auth_info.get("provider")

            # Determine which provider to use based on available info
            if provider == "instagram":
                account_filter = {"provider": "instagram"}
            elif provider == "facebook" or provider == "instagram_business":
                account_filter = {
                    "provider__in": ["instagram_business", "facebook"]
                }
            else:
                # If no specific provider in token, try instagram first,
                # then facebook
                account_filter = {
                    "provider__in": [
                        "instagram",
                        "instagram_business",
                        "facebook",
                    ]
                }

            # Get the appropriate account for the user
            account = (
                Account.objects.filter(user=user, **account_filter)
                .order_by("-updated_at")
                .first()
            )

            if not account:
                return Response(
                    {"error": "No Instagram account found for this user"},
                    status=status.HTTP_404_NOT_FOUND,
                )

            # Determine the correct ID to use
            if account.provider == "instagram":
                instagram_id = account.provider_account_id
            elif account.provider == "instagram_business":
                instagram_id = account.provider_account_id
            else:
                return Response(
                    {"error": "Instagram business account  not available"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            access_token = account.access_token

            if not instagram_id or not access_token:
                return Response(
                    {"error": "Instagram account not connected"},
                    status=status.HTTP_400_BAD_REQUEST,
                )

            demographic_data = InstagramService.get_demographic_insights(
                instagram_id, access_token
            )

            if "error" in demographic_data:
                logger.error(
                    f"Err  Instagram demographics: {demographic_data['error']}"
                )
                return Response(
                    {"error": "Failed to fetch demographic insights"},
                    status=status.HTTP_500_INTERNAL_SERVER_ERROR,
                )

            return Response(demographic_data, status=status.HTTP_200_OK)

        except Exception as e:
            logger.exception(
                "Unexpected error in InstagramDemographicsView", str(e)
            )
            return Response(
                {"error": "An unexpected error occurred"},
                status=status.HTTP_500_INTERNAL_SERVER_ERROR,
            )
