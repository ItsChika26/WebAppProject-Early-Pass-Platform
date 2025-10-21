from django.apps import AppConfig


class PassesConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'passes'

    def ready(self):
        # Import signals to register handlers
        from . import signals  # noqa: F401
