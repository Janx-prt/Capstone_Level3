from django.contrib import admin
from django.urls import path, include

urlpatterns = [
    path("admin/", admin.site.urls),
    path("accounts/", include("django.contrib.auth.urls")),
    # your API package
    path("api/", include("newsroom.api.urls")),
    path("", include(("newsroom.urls", "articles"),
         namespace="articles")),  # << namespaced
]
