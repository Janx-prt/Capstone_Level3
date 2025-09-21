"""
Models for the Newsroom application.

This module defines the core models:

- :class:`User` – a custom user model with roles (Reader, Editor, Journalist).
- :class:`Publisher` – representing publishing organizations.
- :class:`Article` – representing news articles with approval workflow.
- :class:`JournalistProfile` – extended profile for journalists.

Each model includes constraints, relationships, and helper methods
relevant to the newsroom domain.
"""

from django.conf import settings
from django.contrib.auth.models import AbstractUser, Group, Permission
from django.core.exceptions import ValidationError
from django.db import models
from django.db.models import Q
from django.db.models.signals import post_migrate
from django.dispatch import receiver
from django.utils import timezone


# ---------------------------------------------------------------------
# Custom User
# ---------------------------------------------------------------------
class User(AbstractUser):
    """
    Custom user model with roles and newsroom-specific fields.

    Extends :class:`django.contrib.auth.models.AbstractUser` by adding a
    ``role`` field and additional relationships for subscriptions and
    published articles.

    Roles
    -----
    - **READER** – subscribes to publishers/journalists.
    - **EDITOR** – manages content and approvals.
    - **JOURNALIST** – creates and publishes articles.

    Fields
    ------
    role : models.CharField
        The user's role within the newsroom.
    subscriptions_to_publishers : models.ManyToManyField
        Publishers the user subscribes to (reader only).
    subscriptions_to_journalists : models.ManyToManyField
        Journalists the user subscribes to (reader only).
    published_articles : models.ManyToManyField
        Articles independently published by the journalist.
    """

    class Roles(models.TextChoices):
        """Available user roles."""

        READER = "READER", "Reader"
        EDITOR = "EDITOR", "Editor"
        JOURNALIST = "JOURNALIST", "Journalist"

    role = models.CharField(
        max_length=20, choices=Roles.choices, default=Roles.READER
    )

    # --- Reader fields ---
    subscriptions_to_publishers = models.ManyToManyField(
        "Publisher", blank=True, related_name="subscribed_readers"
    )
    subscriptions_to_journalists = models.ManyToManyField(
        "self",
        blank=True,
        symmetrical=False,
        related_name="reader_subscribers",
        limit_choices_to={"role": Roles.JOURNALIST},
    )

    # --- Journalist fields ---
    published_articles = models.ManyToManyField(
        "Article", blank=True, related_name="independent_authors"
    )

    # Helpers
    def is_reader(self) -> bool:
        """Return ``True`` if the user has the Reader role."""
        return self.role == self.Roles.READER

    def is_editor(self) -> bool:
        """Return ``True`` if the user has the Editor role."""
        return self.role == self.Roles.EDITOR

    def is_journalist(self) -> bool:
        """Return ``True`` if the user has the Journalist role."""
        return self.role == self.Roles.JOURNALIST

    def __str__(self) -> str:
        """Return the username as the string representation."""
        return self.get_username()

    def clean(self):
        """
        Validate role-specific constraints.

        - Journalists cannot have reader subscriptions.
        - Readers cannot have published articles.
        - Editors are unrestricted.

        Raises
        ------
        ValidationError
            If role-specific constraints are violated.
        """
        if self.role == self.Roles.JOURNALIST:
            if self.pk and (
                self.subscriptions_to_publishers.exists()
                or self.subscriptions_to_journalists.exists()
            ):
                raise ValidationError(
                    "Journalists cannot have reader subscriptions."
                )

        if self.role == self.Roles.READER:
            if self.pk and self.published_articles.exists():
                raise ValidationError(
                    "Readers cannot have journalist publishing fields."
                )

    def save(self, *args, **kwargs):
        """
        Save the user and assign the user to the group matching their role.

        Each user belongs to exactly one group (Reader, Editor, Journalist).
        Groups and permissions are created in the ``post_migrate`` hook.

        Notes
        -----
        - Overrides :meth:`django.db.models.Model.save`.
        """
        super().save(*args, **kwargs)
        role_to_group = {
            self.Roles.READER: "Reader",
            self.Roles.EDITOR: "Editor",
            self.Roles.JOURNALIST: "Journalist",
        }
        target = role_to_group.get(self.role)
        if target:
            g, _ = Group.objects.get_or_create(name=target)
            self.groups.set([g])


# ---------------------------------------------------------------------
# Publisher
# ---------------------------------------------------------------------
class Publisher(models.Model):
    """
    A publishing organization.

    Fields
    ------
    name : models.CharField
        Unique name of the publisher.
    description : models.TextField
        Optional description of the publisher.
    editors : models.ManyToManyField
        Users with the Editor role.
    journalists : models.ManyToManyField
        Users with the Journalist role.

    Meta
    ----
    ordering : tuple
        Default ordering is by name.
    """

    name = models.CharField(max_length=255, unique=True)
    description = models.TextField(blank=True)

    editors = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="editor_publishers",
        blank=True,
        limit_choices_to={"role": User.Roles.EDITOR},
    )
    journalists = models.ManyToManyField(
        settings.AUTH_USER_MODEL,
        related_name="journalist_publishers",
        blank=True,
        limit_choices_to={"role": User.Roles.JOURNALIST},
    )

    class Meta:
        ordering = ("name",)

    def __str__(self) -> str:
        """Return the publisher's name as string representation."""
        return self.name


# ---------------------------------------------------------------------
# Article
# ---------------------------------------------------------------------
class Article(models.Model):
    """
    A news article authored by a journalist and reviewed by an editor.

    Fields
    ------
    title : models.CharField
        Title of the article.
    body : models.TextField
        Main body text.
    cover_url : models.URLField
        Optional cover image URL.
    publisher : models.ForeignKey
        The publisher associated with the article.
    author : models.ForeignKey
        The journalist author.
    status : models.CharField
        Workflow status (draft, pending, approved, rejected).
    created_at : models.DateTimeField
        Timestamp of article creation.
    updated_at : models.DateTimeField
        Timestamp of last update.
    approved_at : models.DateTimeField
        Timestamp when the article was approved.

    Meta
    ----
    ordering : tuple
        Default ordering: approved_at desc, created_at desc.
    permissions : list
        Custom permission ``can_approve``.
    indexes : list
        Database indexes for common queries.
    """

    class Status(models.TextChoices):
        """Workflow statuses for articles."""

        DRAFT = "DRAFT", "Draft"
        PENDING = "PENDING", "Pending Approval"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    title = models.CharField(max_length=255)
    body = models.TextField()
    cover_url = models.URLField(blank=True)

    publisher = models.ForeignKey(
        Publisher, on_delete=models.CASCADE, related_name="articles"
    )
    author = models.ForeignKey(
        settings.AUTH_USER_MODEL,
        on_delete=models.CASCADE,
        related_name="articles",
        limit_choices_to={"role": User.Roles.JOURNALIST},
    )

    status = models.CharField(
        max_length=20, choices=Status.choices, default=Status.DRAFT
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)
    approved_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ("-approved_at", "-created_at")
        permissions = [
            ("can_approve", "Can approve articles"),
        ]
        indexes = [
            models.Index(fields=("status", "approved_at")),
            models.Index(fields=("publisher", "status")),
            models.Index(fields=("author", "status")),
        ]

    def __str__(self) -> str:
        """Return the article's title with its status as string representation."""
        return f"{self.title} ({self.get_status_display()})"

    @property
    def is_approved(self) -> bool:
        """
        Return whether the article is approved.

        Returns
        -------
        bool
            ``True`` if the status is APPROVED, else ``False``.
        """
        return self.status == self.Status.APPROVED

    def clean(self):
        """
        Validate article fields before saving.

        - Author must have the Journalist role.
        - ``approved_at`` can only be set if status is APPROVED.
        - If approved and timestamp not set, auto-assign now.

        Raises
        ------
        ValidationError
            If constraints are violated.
        """
        if self.author and not getattr(self.author, "is_journalist", lambda: False)():
            raise ValidationError(
                {"author": "Author must have the Journalist role."}
            )

        if self.status != self.Status.APPROVED and self.approved_at:
            raise ValidationError(
                {"approved_at": "approved_at can only be set when status is APPROVED."}
            )

        if self.status == self.Status.APPROVED and not self.approved_at:
            self.approved_at = timezone.now()

    def save(self, *args, **kwargs):
        """
        Save the article after running validation.

        Notes
        -----
        - Calls :meth:`full_clean` before saving to enforce validation.
        """
        self.full_clean()
        super().save(*args, **kwargs)


# ---------------------------------------------------------------------
# Journalist Profile
# ---------------------------------------------------------------------
class JournalistProfile(models.Model):
    """
    Extended profile for journalists.

    Fields
    ------
    user : models.OneToOneField
        Link to the associated user.
    bio : models.TextField
        Optional biography of the journalist.
    avatar : models.ImageField
        Profile image (if Pillow installed), otherwise could use URLField.
    created_at : models.DateTimeField
        Timestamp of profile creation.
    """

    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    bio = models.TextField(blank=True)
    from django.db import models as _m
    avatar = _m.ImageField(upload_to="avatars/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        """Return a string representation showing the username."""
        return f"Profile: {self.user.get_username()}"
