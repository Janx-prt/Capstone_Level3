# newsroom/models.py
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
    class Roles(models.TextChoices):
        READER = "READER", "Reader"
        EDITOR = "EDITOR", "Editor"
        JOURNALIST = "JOURNALIST", "Journalist"

    role = models.CharField(
        max_length=20, choices=Roles.choices, default=Roles.READER)

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
    # Kept for the spec: “articles published independently”.
    # Articles also FK to author; this is a convenience mirror.
    published_articles = models.ManyToManyField(
        "Article", blank=True, related_name="independent_authors"
    )

    # Helpers
    def is_reader(self) -> bool: return self.role == self.Roles.READER
    def is_editor(self) -> bool: return self.role == self.Roles.EDITOR
    def is_journalist(self) -> bool: return self.role == self.Roles.JOURNALIST

    def __str__(self) -> str:
        return self.get_username()

    def clean(self):
        """
        Enforce mutually exclusive reader/journalist fields per brief.
        Editors are unrestricted.
        """
        # If user is journalist, reader subscriptions must be empty
        if self.role == self.Roles.JOURNALIST:
            if self.pk and (
                self.subscriptions_to_publishers.exists()
                or self.subscriptions_to_journalists.exists()
            ):
                raise ValidationError(
                    "Journalists cannot have reader subscriptions.")

        # If user is reader, published content fields must be empty
        if self.role == self.Roles.READER:
            if self.pk and self.published_articles.exists():
                raise ValidationError(
                    "Readers cannot have journalist publishing fields.")

    def save(self, *args, **kwargs):
        """
        Save, then auto-place the user in the single group matching their role.
        (Groups and perms are created in the post_migrate hook below.)
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
            # keep exactly this one role group (simple policy)
            self.groups.set([g])


# ---------------------------------------------------------------------
# Publisher
# ---------------------------------------------------------------------
class Publisher(models.Model):
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
        return self.name


# ---------------------------------------------------------------------
# Article
# ---------------------------------------------------------------------
class Article(models.Model):
    class Status(models.TextChoices):
        DRAFT = "DRAFT", "Draft"
        PENDING = "PENDING", "Pending Approval"
        APPROVED = "APPROVED", "Approved"
        REJECTED = "REJECTED", "Rejected"

    title = models.CharField(max_length=255)
    body = models.TextField()
    # use ImageField if you prefer file uploads
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
        max_length=20, choices=Status.choices, default=Status.DRAFT)
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
        return f"{self.title} ({self.get_status_display()})"

    @property
    def is_approved(self) -> bool:
        return self.status == self.Status.APPROVED

    def clean(self):
        # Ensure author has correct role
        if self.author and not getattr(self.author, "is_journalist", lambda: False)():
            raise ValidationError(
                {"author": "Author must have the Journalist role."})

        # approved_at can only be set when APPROVED
        if self.status != self.Status.APPROVED and self.approved_at:
            raise ValidationError(
                {"approved_at": "approved_at can only be set when status is APPROVED."}
            )

        # If approved and timestamp not set, set it
        if self.status == self.Status.APPROVED and not self.approved_at:
            self.approved_at = timezone.now()

    def save(self, *args, **kwargs):
        self.full_clean()
        super().save(*args, **kwargs)

# ---------------------------------------------------------------------


class JournalistProfile(models.Model):
    user = models.OneToOneField(
        settings.AUTH_USER_MODEL, on_delete=models.CASCADE, related_name="profile"
    )
    bio = models.TextField(blank=True)
    # If you prefer not to install Pillow, switch to URLField instead of ImageField:
    # avatar = models.URLField(blank=True)
    from django.db import models as _m
    avatar = _m.ImageField(upload_to="avatars/", blank=True, null=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"Profile: {self.user.get_username()}"
