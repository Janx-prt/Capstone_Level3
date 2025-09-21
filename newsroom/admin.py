# newsroom/admin.py
from django.contrib import admin
from django.contrib.auth.admin import UserAdmin as DjangoUserAdmin
from django.utils import timezone
from .models import User, Publisher, Article, JournalistProfile


# ---------------------------
# USER
# ---------------------------
@admin.register(User)
class UserAdmin(DjangoUserAdmin):
    fieldsets = DjangoUserAdmin.fieldsets + (
        ("Role & subscriptions", {
            "fields": (
                "role",
                "subscriptions_to_publishers",
                "subscriptions_to_journalists",
                "published_articles",
            )
        }),
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
    list_display = ("name", "editors_count", "journalists_count")
    search_fields = ("name",)
    filter_horizontal = ("editors", "journalists")

    def editors_count(self, obj):
        return obj.editors.count()
    editors_count.short_description = "Editors"

    def journalists_count(self, obj):
        return obj.journalists.count()
    journalists_count.short_description = "Journalists"


# ---------------------------
# ARTICLE
# ---------------------------
@admin.action(description="Approve selected articles (fires signals)")
def approve_articles(modeladmin, request, queryset):
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
    list_display = ("user", "created_at")
    search_fields = ("user__username", "user__email")
