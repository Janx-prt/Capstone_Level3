"""
Django admin customizations for the Newsroom application.

This module registers admin configurations for:

- :class:`~newsroom.models.User`
- :class:`~newsroom.models.Publisher`
- :class:`~newsroom.models.Article`
- :class:`~newsroom.models.JournalistProfile`

It also defines a bulk admin action to approve articles (triggering model
signals by calling ``save()``).
"""

from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils import timezone
from .models import User, Publisher, Article, JournalistProfile


# ---------------------------
# USER
# ---------------------------
@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    """
    Admin configuration for :class:`~newsroom.models.User`.

    Extends :class:`django.contrib.auth.admin.UserAdmin` by adding newsroom-
    specific fields such as role, subscription relationships, and a mirror
    of independently published articles.

    Notes
    -----
    - A "Role & subscriptions" fieldset is appended to the base user fieldsets.
    - The **role** field is added to the add form.
    - Many-to-many fields use the horizontal filter widget.
    """

    fieldsets = DjangoUserAdmin.fieldsets + (
        (
            "Role & subscriptions",
            {
                "fields": (
                    "role",
                    "subscriptions_to_publishers",
                    "subscriptions_to_journalists",
                    "published_articles",
                )
            },
        ),
    )
    add_fieldsets = DjangoUserAdmin.add_fieldsets + (
        (None, {"fields": ("role",)}),
    )

    list_display = ("username", "email", "role", "is_staff", "is_active")
    list_filter = ("role", "is_staff", "is_active")
    search_fields = ("username", "email")
    filter_horizontal = (
        "subscriptions_to_publishers",
        "subscriptions_to_journalists",
        "published_articles",
    )


# ---------------------------
# PUBLISHER
# ---------------------------
@admin.register(Publisher)
class PublisherAdmin(admin.ModelAdmin):
    """
    Admin configuration for :class:`~newsroom.models.Publisher`.

    Displays the publisher name and dynamic counts for related editors and
    journalists. Provides search by name and horizontal filters for the
    many-to-many user relations.
    """

    list_display = ("name", "editors_count", "journalists_count")
    search_fields = ("name",)
    filter_horizontal = ("editors", "journalists")

    def editors_count(self, obj):
        """
        Return the number of editors related to this publisher.

        Parameters
        ----------
        obj : Publisher
            The current publisher row.

        Returns
        -------
        int
            Count of related editors.
        """
        return obj.editors.count()
    editors_count.short_description = "Editors"

    def journalists_count(self, obj):
        """
        Return the number of journalists related to this publisher.

        Parameters
        ----------
        obj : Publisher
            The current publisher row.

        Returns
        -------
        int
            Count of related journalists.
        """
        return obj.journalists.count()
    journalists_count.short_description = "Journalists"


# ---------------------------
# ARTICLE
# ---------------------------
@admin.action(description="Approve selected articles (fires signals)")
def approve_articles(modeladmin, request, queryset):
    """
    Bulk-approve selected articles and persist changes via ``save()``.

    For each selected article that is not already approved, set the status to
    :attr:`~newsroom.models.Article.Status.APPROVED`, ensure
    :attr:`~newsroom.models.Article.approved_at` is populated, and call
    :meth:`~django.db.models.Model.save` so that pre/post-save signals run.

    Parameters
    ----------
    modeladmin : django.contrib.admin.ModelAdmin
        The invoking admin instance.
    request : django.http.HttpRequest
        The current request.
    queryset : django.db.models.QuerySet
        The queryset of selected :class:`~newsroom.models.Article` objects.
    """
    updated = 0
    for a in queryset.exclude(status=Article.Status.APPROVED):
        a.status = Article.Status.APPROVED
        if not a.approved_at:
            a.approved_at = timezone.now()
        # Call save() so pre/post_save signals run (emails, etc.)
        a.save()
        updated += 1
    modeladmin.message_user(request, f"Approved {updated} article(s).")


@admin.register(Article)
class ArticleAdmin(admin.ModelAdmin):
    """
    Admin configuration for :class:`~newsroom.models.Article`.

    Provides list display for key fields, filtering by status/publisher,
    search across title/author/publisher, an approval action, and convenient
    navigation via date hierarchy and ordering.
    """

    list_display = ("title", "publisher", "author",
                    "status", "approved_at", "created_at")
    list_filter = ("status", "publisher")
    search_fields = ("title", "author__username", "publisher__name")
    actions = [approve_articles]
    autocomplete_fields = ("publisher", "author")
    date_hierarchy = "created_at"
    ordering = ("-created_at",)


# ---------------------------
# JOURNALIST PROFILE
# ---------------------------
@admin.register(JournalistProfile)
class JournalistProfileAdmin(admin.ModelAdmin):
    """
    Admin configuration for :class:`~newsroom.models.JournalistProfile`.

    Shows the related user and creation timestamp, with search on
    username and email.
    """

    list_display = ("user", "created_at")
    search_fields = ("user__username", "user__email")
