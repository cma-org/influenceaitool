"""
Database models for Facebook Service
"""

from django.db import models
from users.models import Account

# Create your models here.


class IGUser(models.Model):
    """
    Facebook login user model - stores Instagram profile information
    linked to an Account model that handles authentication
    """

    account = models.OneToOneField(Account, on_delete=models.CASCADE)
    user_scope_id = models.CharField(max_length=255, blank=True, null=True)
    biography = models.TextField(blank=True, null=True)
    followers_count = models.IntegerField(null=True, blank=True)
    follows_count = models.IntegerField(null=True, blank=True)
    has_profile_pic = models.BooleanField(default=False)
    is_published = models.BooleanField(default=False)
    media_count = models.IntegerField(null=True, blank=True)
    name = models.CharField(max_length=255, blank=True, null=True)
    profile_picture_url = models.URLField(
        max_length=2000, blank=True, null=True
    )
    username = models.CharField(max_length=255, blank=True, null=True)
    website = models.URLField(max_length=2000, blank=True, null=True)

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    def __str__(self):
        return f"{self.username or 'Unnamed User'} ({self.name or 'No Name'})"

    class Meta:
        verbose_name = "Facebook User"
        verbose_name_plural = "Facebook Users"
        indexes = [
            models.Index(fields=["username"]),
        ]
