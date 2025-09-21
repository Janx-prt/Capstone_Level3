"""
Project-level URL configuration.

This module defines the root URL routes for the project,
including:

- Django admin interface
- Authentication system
- Newsroom API endpoints
- Newsroom app views (namespaced as ``articles``)
"""

from django.contrib import admin
from django.urls import path, include

#: URL patterns for the project.
urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    # your API package
    path("api/", include("newsroom.api.urls")),
    path(
        "",
        include(("newsroom.urls", "articles"), namespace="articles"),
    ),  # << namespaced
]
