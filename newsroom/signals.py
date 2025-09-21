"""
Signal handlers for the Newsroom application.

This module defines Django signal receivers that handle:

- Automatic creation of :class:`~newsroom.models.JournalistProfile` when a
  user with the Journalist role is created or updated.
- Tracking of article approval transitions.
- Sending email notifications to subscribers and authors when articles are
  approved.
"""

from django.conf import settings
from django.core.mail import send_mass_mail
from django.db.models.signals import pre_save, post_save
from django.db.models import Q
from django.dispatch import receiver
from django.utils import timezone

from .models import Article, JournalistProfile, User


# -----------------------------------------------------------------------------
# Create a JournalistProfile for users with the Journalist role
# -----------------------------------------------------------------------------
@receiver(post_save, sender=User)
def ensure_journalist_profile(sender, instance: User, created, **kwargs):
    """
    Ensure that a JournalistProfile exists for journalist users.

    Triggered after a :class:`~newsroom.models.User` is saved.

    Parameters
    ----------
    sender : type
        The model class (:class:`~newsroom.models.User`).
    instance : User
        The user instance being saved.
    created : bool
        Whether this instance was newly created.
    **kwargs
        Additional keyword arguments passed by the signal.
    """
    if instance.is_journalist():
        JournalistProfile.objects.get_or_create(user=instance)
    # If role changes away from Journalist, the profile is retained by default.


# -----------------------------------------------------------------------------
# Mark when an Article is newly approved (so post_save can react once)
# -----------------------------------------------------------------------------
@receiver(pre_save, sender=Article)
def mark_just_approved(sender, instance: Article, **kwargs):
    """
    Mark articles that transition to the APPROVED status.

    Sets a private flag ``_just_approved`` on the instance so that the
    ``post_save`` handler can send notifications only once.

    Parameters
    ----------
    sender : type
        The model class (:class:`~newsroom.models.Article`).
    instance : Article
        The article instance being saved.
    **kwargs
        Additional keyword arguments passed by the signal.
    """
    instance._just_approved = False

    if not instance.pk:
        if instance.status == Article.Status.APPROVED:
            instance.approved_at = instance.approved_at or timezone.now()
            instance._just_approved = True
        return

    try:
        previous = Article.objects.get(pk=instance.pk)
    except Article.DoesNotExist:
        return

    if (
        previous.status != Article.Status.APPROVED
        and instance.status == Article.Status.APPROVED
    ):
        instance.approved_at = instance.approved_at or timezone.now()
        instance._just_approved = True


# -----------------------------------------------------------------------------
# Helpers for notifications
# -----------------------------------------------------------------------------
def _subscriber_emails(article: Article):
    """
    Return emails of all readers subscribed to the publisher or journalist.

    Parameters
    ----------
    article : Article
        The article being approved.

    Returns
    -------
    list[str]
        A list of unique email addresses for subscriber readers.
    """
    readers_qs = User.objects.filter(role=User.Roles.READER).filter(
        Q(subscriptions_to_publishers=article.publisher)
        | Q(subscriptions_to_journalists=article.author)
    ).distinct().values_list("email", flat=True)

    return [e for e in readers_qs if e]


# -----------------------------------------------------------------------------
# After save: if just approved, notify subscribers (and optionally the author)
# -----------------------------------------------------------------------------
@receiver(post_save, sender=Article)
def on_article_approved(sender, instance: Article, created, **kwargs):
    """
    Send notifications when an article is approved.

    If the article has transitioned to APPROVED, this handler:

    - Emails all subscribed readers (publisher or journalist subscribers).
    - Optionally emails the author if they were not already included.

    Parameters
    ----------
    sender : type
        The model class (:class:`~newsroom.models.Article`).
    instance : Article
        The article instance that was saved.
    created : bool
        Whether the instance was newly created.
    **kwargs
        Additional keyword arguments passed by the signal.
    """
    if not getattr(instance, "_just_approved", False):
        return

    from_email = getattr(settings, "DEFAULT_FROM_EMAIL",
                         "no-reply@example.com")
    subject = f"{instance.publisher.name}: {instance.title}"

    preview = (
        instance.body if len(
            instance.body) <= 500 else f"{instance.body[:500]}..."
    )
    recipients = _subscriber_emails(instance)

    # Notify subscribers
    if recipients:
        datatuple = [(subject, preview, from_email, [addr])
                     for addr in recipients]
        try:
            send_mass_mail(datatuple, fail_silently=True)
        except Exception:
            # Never block the save operation due to email errors
            pass

    # Optionally notify the author too
    author_email = getattr(instance.author, "email", "") or ""
    if author_email and author_email not in recipients:
        try:
            send_mass_mail(
                [
                    (
                        f"Article approved: {instance.title}",
                        f"Hi {instance.author.get_username()},\n\n"
                        f"Your article '{instance.title}' at {instance.publisher.name} was approved.",
                        from_email,
                        [author_email],
                    )
                ],
                fail_silently=True,
            )
        except Exception:
            pass
