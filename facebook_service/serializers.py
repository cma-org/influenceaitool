"""
Serializers for Facebook and Instagram models
"""

from rest_framework import serializers
from .models import FacebookPage, InstagramBusinessAccount, InstagramInsights


class FacebookAuthSerializer(serializers.Serializer):
    """
    Serializer for Facebook authentication request
    """

    access_token = serializers.CharField(required=True)
    user_type = serializers.CharField(required=False, default="brand")


class FacebookPageSerializer(serializers.ModelSerializer):
    """
    Serializer for FacebookPage model
    """

    class Meta:
        model = FacebookPage
        fields = [
            "id",
            "page_id",
            "name",
            "token_expires_at",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]


class InstagramAccountSerializer(serializers.ModelSerializer):
    """
    Serializer for InstagramBusinessAccount model
    """

    page_name = serializers.SerializerMethodField()
    page_id = serializers.SerializerMethodField()

    class Meta:
        model = InstagramBusinessAccount
        fields = [
            "id",
            "instagram_id",
            "username",
            "name",
            "profile_picture_url",
            "biography",
            "website",
            "follows_count",
            "followers_count",
            "media_count",
            "is_verified",
            "is_primary",
            "page_id",
            "page_name",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "created_at", "updated_at"]

    def get_page_name(self, obj):
        return obj.facebook_page.name

    def get_page_id(self, obj):
        return obj.facebook_page.page_id


class InstagramInsightsSerializer(serializers.ModelSerializer):
    """
    Serializer for InstagramInsights model
    """

    instagram_username = serializers.SerializerMethodField()

    class Meta:
        model = InstagramInsights
        fields = [
            "id",
            "instagram_username",
            "date",
            "follower_count",
            "reach",
            "impressions",
            "profile_views",
        ]
        read_only_fields = ["id"]

    def get_instagram_username(self, obj):
        return obj.instagram_account.username
