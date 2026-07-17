from django.apps import AppConfig


class ManufacturingConfig(AppConfig):
    default_auto_field = "django.db.models.BigAutoField"
    name = "apps.manufacturing"

    def ready(self):
        import apps.manufacturing.signals  # noqa: F401
