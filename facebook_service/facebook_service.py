"""
Make authenticated requests to Facebook API
"""

import logging
import requests
from datetime import timedelta
from django.conf import settings
from django.utils import timezone


logger = logging.getLogger(__name__)


class FacebookService:
    """
    Methods to return data from Facebook API,
    with access_token
    """

    HOST = "https://graph.facebook.com"
    BASE_URL = "https://graph.facebook.com/v22.0"

    @staticmethod
    def debug_token(access_token):
        """
        debug token
        """
        try:
            endpoint = f"{FacebookService.HOST}/debug_token"
            params = {
                "input_token": access_token,
                "access_token": access_token,
            }

            response = requests.get(endpoint, params=params, timeout=60)
            response.raise_for_status()
            data = response.json()
        except requests.exceptions.RequestException as e:
            logger.error(f"Error verifying token: {str(e)}")
            print("errorrr: ", e.response.json())
            return e.response.json()

        return data

    @staticmethod
    def exchange_for_long_lived_token(access_token):
        """
        Exchange short-lived token for a long-lived token (valid for 60 days)
        """
        try:
            endpoint = f"{FacebookService.BASE_URL}/oauth/access_token"
            params = {
                "grant_type": "fb_exchange_token",
                "client_id": settings.APP_ID,
                "client_secret": settings.APP_SECRET,
                "fb_exchange_token": access_token,
            }

            response = requests.get(endpoint, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            # The response includes access_token and expires_in fields
            long_lived_token = data.get("access_token")
            expires_in = data.get("expires_in", 0)

            # Calculate expiration timestamp
            expiration_time = timezone.now() + timedelta(seconds=expires_in)

            return {
                "success": True,
                "access_token": long_lived_token,
                "expires_in": expires_in,
                "expires_at": expiration_time,
            }
        except requests.exceptions.RequestException as e:
            logger.error(f"Error exchanging for long-lived token: {str(e)}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_ig_business_account(page_id, access_token):
        """
        Get Ig business account for the specified page
        """
        try:
            fields = [
                "instagram_business_account",
            ]
            endpoint = f"{FacebookService.BASE_URL}/{page_id}"
            params = {
                "access_token": access_token,
                "fields": ",".join(fields),
            }

            response = requests.get(endpoint, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            print("ig business account", data)

            return {"success": True, "data": data}
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting IG business account: {str(e)}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_connected_accounts(access_token):
        """
        Get user's Instagram Business accounts via connected Facebook Pages
        """
        try:
            fields = [
                "id",
                "name",
                "access_token",
                "instagram_business_account",
            ]
            endpoint = f"{FacebookService.BASE_URL}/me/accounts"
            params = {
                "access_token": access_token,
                "fields": ",".join(fields),
            }

            response = requests.get(endpoint, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()
            print("instagram accounts", data)

            # Filter pages with Instagram Business accounts
            pages_with_instagram = []
            for page in data.get("data", []):
                if "instagram_business_account" in page:
                    pages_with_instagram.append(page)
            data["pages"] = pages_with_instagram

            return {"success": True, "data": data}
        except requests.exceptions.RequestException as e:
            logger.error(f"Error getting connected accounts: {str(e)}")
            return {"success": False, "error": str(e)}

    @staticmethod
    def get_instagram_user_profile(instagram_id, access_token):
        """
        Fetch Instagram user profile
        """
        fields = [
            "biography",
            "followers_count",
            "follows_count",
            "has_profile_pic",
            "id",
            "is_published",
            "media_count",
            "name",
            "profile_picture_url",
            "username",
            "website",
        ]

        endpoint = f"https://graph.facebook.com/v22.0/{instagram_id}"
        params = {
            "access_token": access_token,
            "fields": "".join(fields),
        }

        response = requests.get(endpoint, params=params, timeout=60)
        response.raise_for_status()
        data = response.json()

        return data

    @staticmethod
    def verify_me(access_token):
        """
        Verify Facebook access token and return basic user information
        """
        try:
            endpoint = f"{FacebookService.BASE_URL}/me"
            params = {
                "access_token": access_token,
                "fields": "id,name,email,first_name,last_name",
            }

            response = requests.get(endpoint, params=params, timeout=30)
            response.raise_for_status()
            data = response.json()

        except requests.exceptions.RequestException as e:
            logger.error(f"Error verifying token: {str(e)}")
            print("errorrr: ", e.response.json())
            return e.response.json()
        return {"success": True, "data": data}
