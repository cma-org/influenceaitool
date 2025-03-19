from django.urls import path
from .views import UserMeView

urlpatterns = [
    path("user/me/", UserMeView.as_view(), name="user-me"),
]
