from rest_framework import serializers
from .models import User, Account


class AccountSerializer(serializers.ModelSerializer):
    class Meta:
        model = Account
        fields = [
            "id",
            "type",
            "description",
            "provider",
            "provider_account_id",
            "user_type",
            "created_at",
        ]
        read_only_fields = ["id", "created_at"]


class UserSerializer(serializers.ModelSerializer):
    accounts = AccountSerializer(many=True, read_only=True)

    class Meta:
        model = User
        fields = [
            "id",
            "name",
            "username",
            "user_type",
            "email",
            "email_verified",
            "image",
            "accounts",
            "created_at",
            "updated_at",
        ]
        read_only_fields = ["id", "email_verified", "created_at", "updated_at"]


class UserCreateSerializer(serializers.ModelSerializer):
    """Create User with magicLink Serializers"""

    class Meta:
        model = User
        fields = ["id", "email", "user_type", "username"]
