from django.core.mail import send_mail
from django.conf import settings


def notify(subject, message, recipients):
    if not recipients:
        return 0
    return send_mail(subject, message, settings.DEFAULT_FROM_EMAIL, recipients, fail_silently=True)
