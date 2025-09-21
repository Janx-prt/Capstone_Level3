"""
URL configuration for the Newsroom app.

This module defines namespaced routes (``articles``) for:

- Public site (landing page, article detail)
- User dashboard
- Journalist CRUD (create, update, delete articles)
- Editor review and approval
- Authentication (signup; login/logout provided at project level)
"""

from django.urls import path
from .views import (
    LandingView,
    ArticleDetailView,
    DashboardView,
    # Journalist CRUD
    ArticleCreateView,
    ArticleUpdateView,
    ArticleDeleteView,
    # Editor review/approve
    ReviewQueueView,
    approve_article,
    # Auth
    SignUpView,
)

#: Application namespace for URL reversing.
app_name = "articles"

#: URL patterns for the Newsroom app.
urlpatterns = [
    # Public site
    path("", LandingView.as_view(), name="landing"),
    path("articles/<int:pk>/", ArticleDetailView.as_view(), name="article-detail"),

    # Dashboard
    path("dashboard/", DashboardView.as_view(), name="dashboard"),

    # Journalist CRUD
    path("articles/new/", ArticleCreateView.as_view(), name="article-create"),
    path("articles/<int:pk>/edit/",
         ArticleUpdateView.as_view(), name="article-edit"),
    path("articles/<int:pk>/delete/",
         ArticleDeleteView.as_view(), name="article-delete"),

    # Editor review & approve
    path("review/", ReviewQueueView.as_view(), name="review"),
    path("articles/<int:pk>/approve/", approve_article, name="article-approve"),

    # Signup (login/logout are handled via django.contrib.auth.urls at project level)
    path("signup/", SignUpView.as_view(), name="signup"),
]
