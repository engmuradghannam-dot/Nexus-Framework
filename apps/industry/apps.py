from django.apps import AppConfig


class IndustryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.industry'

    def ready(self):
        import apps.industry.signals  # noqa: F401
