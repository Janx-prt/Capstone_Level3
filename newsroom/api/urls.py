from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ArticleViewSet, PublisherViewSet

router = DefaultRouter()
router.register(r"articles", ArticleViewSet, basename="article")
router.register(r"publishers", PublisherViewSet, basename="publisher")

urlpatterns = [
    path("", include(router.urls)),
    path("auth/", include("rest_framework.urls")),  # browsable API login
]
