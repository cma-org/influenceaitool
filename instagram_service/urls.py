"""
API endpoints
"""

from django.urls import path
from .views import InstagramMediaView, InstagramMediaDetailView
from .views import (
    InstagramAccountInsightsView,
    InstagramFollowersGrowthView,
    InstagramPostEngagementsView,
    InstagramCurrentMonthLikesView,
    InstagramDemographicsView,
)

urlpatterns = [
    path("media/", InstagramMediaView.as_view(), name="instagram-media"),
    path(
        "media/<str:media_id>/",
        InstagramMediaDetailView.as_view(),
        name="instagram-media-detail",
    ),
    path(
        "insights/account/",
        InstagramAccountInsightsView.as_view(),
        name="instagram-account-insights",
    ),
    path(
        "insights/followers-growth/",
        InstagramFollowersGrowthView.as_view(),
        name="instagram-followers-growth",
    ),
    path(
        "insights/post-engagements/",
        InstagramPostEngagementsView.as_view(),
        name="instagram-post-engagements",
    ),
    path(
        "insights/current-month-likes/",
        InstagramCurrentMonthLikesView.as_view(),
        name="instagram-current-month-likes",
    ),
    path(
        "insights/demographics/",
        InstagramDemographicsView.as_view(),
        name="instagram-demographics",
    ),
]
