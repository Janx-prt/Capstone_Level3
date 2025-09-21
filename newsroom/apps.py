"""
Django application configuration for the Newsroom app.

This module defines the application configuration used by Django to
initialize the Newsroom app. It ensures that signal handlers are
registered automatically when the app is ready.
"""

from django.apps import AppConfig


class NewsroomConfig(AppConfig):
    """
    Configuration class for the Newsroom application.

    Attributes
    ----------
    default_auto_field : str
        Specifies the default type of auto-created primary keys for models
        in this app. Uses ``BigAutoField`` for scalability.
    name : str
        The name of the Django application (``newsroom``).
    """

    default_auto_field = "django.db.models.BigAutoField"
    name = "newsroom"

    def ready(self):
        """
        Import and register signal handlers for the Newsroom app.

        This method is executed when the Django application registry
        is fully populated. Importing ``newsroom.signals`` ensures that
        model signals (such as pre-save, post-save, etc.) are connected
        to their respective handlers.

        Notes
        -----
        - The ``# noqa: F401`` comment prevents linters from flagging
          the unused import, since the import is necessary for side effects.
        """
        # ensure signal handlers are registered
        import newsroom.signals  # noqa: F401
