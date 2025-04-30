"""
Database models for Facebook and Instagram integration
"""

from django.db import models
from users.models import Account


class FacebookPage(models.Model):
    """
    Model to store Facebook Page information
    """

    account = models.ForeignKey(
        Account, on_delete=models.CASCADE, related_name="facebook_pages"
    )
    page_id = models.CharField(max_length=255, unique=True)
    name = models.CharField(max_length=255)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Facebook Page"
        verbose_name_plural = "Facebook Pages"
        indexes = [
            models.Index(fields=["page_id"]),
        ]

    def __str__(self):
        return f"{self.name} ({self.page_id})"


class InstagramBusinessAccount(models.Model):
    """
    Model to store Instagram Business Account information
    """

    facebook_page = models.OneToOneField(
        FacebookPage,
        on_delete=models.CASCADE,
        related_name="instagram_account",
    )
    instagram_id = models.CharField(max_length=255, unique=True)
    username = models.CharField(max_length=255)
    name = models.CharField(max_length=255, null=True, blank=True)
    profile_picture_url = models.URLField(
        max_length=2000, null=True, blank=True
    )
    biography = models.TextField(null=True, blank=True)
    website = models.URLField(max_length=2000, null=True, blank=True)
    follows_count = models.PositiveIntegerField(default=0)
    followers_count = models.PositiveIntegerField(default=0)
    media_count = models.PositiveIntegerField(default=0)
    is_verified = models.BooleanField(default=False)
    is_primary = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name = "Instagram Business Account"
        verbose_name_plural = "Instagram Business Accounts"
        indexes = [
            models.Index(fields=["instagram_id"]),
            models.Index(fields=["username"]),
        ]

    def __str__(self):
        return f"{self.username} ({self.instagram_id})"

    def save(self, *args, **kwargs):
        # If this is the first Instagram account
        # for the user, mark it as primary
        if not InstagramBusinessAccount.objects.filter(
            facebook_page__account=self.facebook_page.account
        ).exists():
            self.is_primary = True
        super().save(*args, **kwargs)


class InstagramInsights(models.Model):
    """
    Model to store Instagram insights data
    """

    instagram_account = models.ForeignKey(
        InstagramBusinessAccount,
        on_delete=models.CASCADE,
        related_name="insights",
    )
    date = models.DateField()
    follower_count = models.PositiveIntegerField()
    reach = models.PositiveIntegerField()
    impressions = models.PositiveIntegerField()
    profile_views = models.PositiveIntegerField()

    class Meta:
        verbose_name = "Instagram Insights"
        verbose_name_plural = "Instagram Insights"
        unique_together = (("instagram_account", "date"),)
        indexes = [
            models.Index(fields=["date"]),
        ]

    def __str__(self):
        return f"{self.instagram_account.username} - {self.date}"
