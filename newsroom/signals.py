# newsroom/signals.py
from django.conf import settings
from django.core.mail import send_mass_mail
from django.db.models.signals import pre_save, post_save
from django.db.models import Q
from django.dispatch import receiver
from django.utils import timezone

from .models import Article, JournalistProfile, User


# -----------------------------------------------------------------------------
# Create a JournalistProfile for users with the Journalist role
# (handles both user creation and role changes)
# -----------------------------------------------------------------------------
@receiver(post_save, sender=User)
def ensure_journalist_profile(sender, instance: User, created, **kwargs):
    if instance.is_journalist():
        JournalistProfile.objects.get_or_create(user=instance)
    # If a user stops being a journalist, we keep the profile by default.
    # If you prefer to remove it, add:
    # else:
    #     JournalistProfile.objects.filter(user=instance).delete()


# -----------------------------------------------------------------------------
# Mark when an Article is newly approved (so post_save can react once)
# -----------------------------------------------------------------------------
@receiver(pre_save, sender=Article)
def mark_just_approved(sender, instance: Article, **kwargs):
    # Default to False; set True only on transitions to APPROVED
    instance._just_approved = False

    # New object (no PK yet)
    if not instance.pk:
        if instance.status == Article.Status.APPROVED:
            instance.approved_at = instance.approved_at or timezone.now()
            instance._just_approved = True
        return

    # Existing object: compare previous status from DB
    try:
        previous = Article.objects.get(pk=instance.pk)
    except Article.DoesNotExist:
        return

    if previous.status != Article.Status.APPROVED and instance.status == Article.Status.APPROVED:
        instance.approved_at = instance.approved_at or timezone.now()
        instance._just_approved = True


# -----------------------------------------------------------------------------
# Helpers for notifications
# -----------------------------------------------------------------------------
def _subscriber_emails(article: Article):
    """
    All READER users who are subscribed to the article's publisher OR journalist.
    """
    readers_qs = User.objects.filter(role=User.Roles.READER).filter(
        Q(subscriptions_to_publishers=article.publisher) |
        Q(subscriptions_to_journalists=article.author)
    ).distinct().values_list("email", flat=True)

    return [e for e in readers_qs if e]  # drop empty emails


# -----------------------------------------------------------------------------
# After save: if just approved, notify subscribers (and optionally the author)
# -----------------------------------------------------------------------------
@receiver(post_save, sender=Article)
def on_article_approved(sender, instance: Article, created, **kwargs):
    if not getattr(instance, "_just_approved", False):
        return

    from_email = getattr(settings, "DEFAULT_FROM_EMAIL",
                         "no-reply@example.com")
    subject = f"{instance.publisher.name}: {instance.title}"

    preview = instance.body if len(
        instance.body) <= 500 else f"{instance.body[:500]}..."
    recipients = _subscriber_emails(instance)

    # Email subscribers (publisher/journalist subscribers)
    if recipients:
        datatuple = [(subject, preview, from_email, [addr])
                     for addr in recipients]
        try:
            send_mass_mail(datatuple, fail_silently=True)
        except Exception:
            # never block the save
            pass

    # Optionally notify the author too (if they have an email and weren't included)
    author_email = getattr(instance.author, "email", "") or ""
    if author_email and author_email not in recipients:
        try:
            send_mass_mail([(f"Article approved: {instance.title}",
                             f"Hi {instance.author.get_username()},\n\n"
                             f"Your article '{instance.title}' at {instance.publisher.name} was approved.",
                             from_email, [author_email])],
                           fail_silently=True)
        except Exception:
            pass
