"""
Utility functions for sending email notifications.

This module provides a simple wrapper around Django's
:func:`django.core.mail.send_mail` to send notification
emails from the application.
"""

from django.core.mail import send_mail
from django.conf import settings


def notify(subject, message, recipients):
    """
    Send an email notification to the specified recipients.

    This function wraps :func:`django.core.mail.send_mail` and
    ensures that the sender address comes from
    ``settings.DEFAULT_FROM_EMAIL``. If no recipients are provided,
    the function will return ``0`` without sending anything.

    Parameters
    ----------
    subject : str
        The subject line of the email.
    message : str
        The plain-text body of the email.
    recipients : list[str] | tuple[str]
        A list or tuple of recipient email addresses.

    Returns
    -------
    int
        The number of successfully delivered messages (as returned by
        :func:`django.core.mail.send_mail`). Returns ``0`` if no
        recipients are given.

    Notes
    -----
    - The ``fail_silently=True`` flag is used, meaning errors during
      sending will not raise exceptions.
    """
    if not recipients:
        return 0
    return send_mail(
        subject,
        message,
        settings.DEFAULT_FROM_EMAIL,
        recipients,
        fail_silently=True,
    )
