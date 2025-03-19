"""
Models in Database
"""

import uuid
from django.db import models
from django.contrib.auth.models import AbstractUser
from django.utils.translation import gettext_lazy as _


class User(AbstractUser):
    """User in the system"""

    USER_TYPE_CHOICES = (
        ("influencer", "Influencer"),
        ("brand", "Brand"),
        ("admin", "Admin"),
    )

    name = models.CharField(_("name"), max_length=255, blank=True, null=True)
    username = models.CharField(_("username"), max_length=255, unique=True)
    user_type = models.CharField(
        choices=USER_TYPE_CHOICES, default="influencer"
    )
    email = models.EmailField(
        _("email address"), unique=True, blank=True, null=True
    )
    email_verified = models.DateTimeField(blank=True, null=True)
    image = models.URLField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    def __str__(self):
        return self.email


class Account(models.Model):
    """User's social media accounts"""

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="accounts"
    )
    description = models.CharField(max_length=445, blank=True, null=True)
    type = models.CharField(max_length=50)  # 'oauth', 'email', etc.
    provider = models.CharField(max_length=50)  # 'instagram', 'facebook', etc.
    provider_account_id = models.CharField(max_length=255)
    refresh_token = models.TextField(blank=True, null=True)
    access_token = models.TextField(blank=True, null=True)
    expires_at = models.IntegerField(blank=True, null=True)
    token_type = models.CharField(max_length=50, blank=True, null=True)
    scope = models.TextField(blank=True, null=True)
    session_state = models.CharField(max_length=255, blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        unique_together = (("provider", "provider_account_id"),)

    def __str__(self):
        return f"{self.provider} - {self.provider_account_id}"


class MagicLink(models.Model):
    """
    Magic link tokens for passwordless authentication
    """

    user = models.ForeignKey(
        User, on_delete=models.CASCADE, related_name="magiclinks"
    )
    token = models.UUIDField(default=uuid.uuid4, editable=False, unique=True)
    email = models.EmailField()
    user_type = models.CharField(
        max_length=20, choices=User.USER_TYPE_CHOICES, default="influencer"
    )
    is_used = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    expires_at = models.DateTimeField()

    def __str__(self):
        return f"{self.email} - {self.token}"
