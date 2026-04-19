from django.urls import include, path
from rest_framework.routers import DefaultRouter

from .views import CommentViewSet, CaptchaView

router = DefaultRouter()

router.register(r"", CommentViewSet, basename="comments")

urlpatterns = [
    path("captcha/", CaptchaView.as_view(), name="captcha"),
    path("", include(router.urls)),
]
