# newsroom/urls.py
from django.urls import path
from .views import (
    LandingView,
    ArticleDetailView,
    DashboardView,
    # Journalist CRUD
    ArticleCreateView,
    ArticleUpdateView,
    ArticleDeleteView,
    # Editor review/approve (handled in the view = Option 2)
    ReviewQueueView,
    approve_article,
    # Auth
    SignUpView,
)

app_name = "articles"  # namespaced URLs

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

    # Editor review & approve (Option 2: approval logic in this view)
    path("review/", ReviewQueueView.as_view(), name="review"),
    path("articles/<int:pk>/approve/", approve_article, name="article-approve"),

    # Signup (login/logout are from django.contrib.auth.urls in project urls)
    path("signup/", SignUpView.as_view(), name="signup"),
]
