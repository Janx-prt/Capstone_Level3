# newsroom/apps.py
from django.apps import AppConfig


class NewsroomConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "newsroom"

    def ready(self):
        # ensure signal handlers are registered
        import newsroom.signals  # noqa: F401
