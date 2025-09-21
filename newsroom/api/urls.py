"""
URL configuration for the Newsroom API.

This module registers API routes for:

- :class:`~newsroom.views.ArticleViewSet`
- :class:`~newsroom.views.PublisherViewSet`

It also includes authentication endpoints for the Django REST Framework
browsable API.
"""

from django.urls import path, include
from rest_framework.routers import DefaultRouter
from .views import ArticleViewSet, PublisherViewSet

#: Default router for automatically generating RESTful routes.
router = DefaultRouter()
router.register(r"articles", ArticleViewSet, basename="article")
router.register(r"publishers", PublisherViewSet, basename="publisher")

#: URL patterns for the Newsroom API.
urlpatterns = [
    path("", include(router.urls)),
    path("auth/", include("rest_framework.urls")),  # browsable API login
]
