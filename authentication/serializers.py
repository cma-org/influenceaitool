"""
Authentication Serializers
"""

from rest_framework import serializers
from rest_framework_simplejwt.serializers import TokenObtainPairSerializer
from users.models import User


class MagicLinkRequestSerializer(serializers.Serializer):
    """
    Serializer for magic link request
    """

    email = serializers.EmailField()
    user_type = serializers.ChoiceField(choices=User.USER_TYPE_CHOICES)

    def to_internal_value(self, data):
        """
        Handle potential case issues with user_type
        """
        if "user_type" in data and isinstance(data["user_type"], str):
            data["user_type"] = data["user_type"].lower()
        return super().to_internal_value(data)


class MagicLinkVerifySerializer(serializers.Serializer):
    token = serializers.UUIDField()


class CustomTokenObtainPairSerializer(TokenObtainPairSerializer):
    """
    JWT token generation serializer
    """

    @classmethod
    def get_token(cls, user):
        token = super().get_token(user)

        # Add custom claims to token
        token["email"] = user.email
        token["name"] = user.name
        token["user_type"] = user.user_type

        # Add provider info if available (for social logins)
        accounts = user.accounts.all()
        if accounts.exists():
            # Get the most recently used account
            latest_account = accounts.order_by("-updated_at").first()
            token["provider"] = latest_account.provider
            token["provider_account_id"] = latest_account.provider_account_id

        return token


class SocialLoginSerializer(serializers.Serializer):
    """
    Social Login Serializer
    """

    code = serializers.CharField()
    user_type = serializers.CharField(
        required=False, default="influencer"
    )  # 'influencer' or 'brand'


class MagicLinkAuthUserSerializer(serializers.Serializer):
    """
    Magic link auth user serializer
    """

    token = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "token"]
        read_only_fields = ["id", "email", "token"]

    def get_token(self, user):
        """
        Get token from user
        """
        tokens = CustomTokenObtainPairSerializer.get_token(user)
        return {
            "access": str(tokens.access_token),
            "refresh": str(tokens),
        }


class SocialAuthUserSerializer(serializers.ModelSerializer):
    """
    Craeted for Facebbook
    """

    token = serializers.SerializerMethodField()

    class Meta:
        model = User
        fields = ["id", "email", "name", "image", "token"]
        read_only_fields = ["id", "email", "name", "image", "token"]

    def get_token(self, user):
        """
        Get token from user
        """
        tokens = CustomTokenObtainPairSerializer.get_token(user)
        return {
            "access": str(tokens.access_token),
            "refresh": str(tokens),
        }
