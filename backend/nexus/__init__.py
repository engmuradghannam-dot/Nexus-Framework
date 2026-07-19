# Ensure the Celery app is loaded when Django starts, so shared_task uses it.
try:
    from .celery import app as celery_app

    __all__ = ("celery_app",)
except Exception:
    # Celery is optional in some environments (e.g. minimal test images).
    __all__ = ()
