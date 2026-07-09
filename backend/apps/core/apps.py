from django.apps import AppConfig


class CoreConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.core'
    verbose_name = 'Core System'

    def ready(self):
        import apps.core.admin  # noqa: F401
        import apps.core.signals  # noqa: F401
