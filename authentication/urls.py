from django.urls import path
from rest_framework_simplejwt.views import TokenRefreshView
from .views import (
    CustomTokenObtainPairView,
    InstagramLoginView,
    InstagramAuthCallbackView,
    GenerateMagicLinkView,
    VerifyMagicLinkView,
)

urlpatterns = [
    # JWT token endpoints
    path(
        "token/", CustomTokenObtainPairView.as_view(), name="token_obtain_pair"
    ),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
    # Instagram auth endpoints (for influencers)
    path(
        "instagram/login/",
        InstagramLoginView.as_view(),
        name="instagram_login",
    ),
    path(
        "instagram/callback/",
        InstagramAuthCallbackView.as_view(),
        name="instagram_callback",
    ),
    path(
        "magic-link/request/",
        GenerateMagicLinkView.as_view(),
        name="magic-link-request",
    ),
    path(
        "magic-link/verify/",
        VerifyMagicLinkView.as_view(),
        name="magic-link-request",
    ),
]

"""

curl -H 'Content-Type: application/json' \
      -d '{ "email":"foo@example.com","user_type":"influencer"}' \
      -X POST \
      http://localhost:8000/api/auth/magic-link/request/
"""
