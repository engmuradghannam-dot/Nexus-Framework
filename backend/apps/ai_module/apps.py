from django.apps import AppConfig


class AiModuleConfig(AppConfig):
    default_auto_field = 'django.db.models.BigAutoField'
    name = 'apps.ai_module'
    verbose_name = 'AI Engine'

    def ready(self):
        import apps.ai_module.admin  # noqa: F401
