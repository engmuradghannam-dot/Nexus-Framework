from django.apps import AppConfig


class IndustryConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.industry'
    verbose_name = 'Industry Intelligence'

    def ready(self):
        import apps.industry.admin  # noqa: F401
        import apps.industry.signals  # noqa: F401
