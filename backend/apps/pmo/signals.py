"""PMO Signals"""

from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import Portfolio, Project, Task


@receiver(post_save, sender=Project)
def project_post_save(sender, instance, created, **kwargs):
    """Handle project post-save actions"""
    if created:
        pass


@receiver(post_delete, sender=Project)
def project_post_delete(sender, instance, **kwargs):
    """Handle project post-delete cleanup"""
    pass


@receiver(post_save, sender=Task)
@receiver(post_delete, sender=Task)
def task_recalc_project_progress(sender, instance, **kwargs):
    """Keep Project.progress in sync with task completion (see
    Project.recalculate_progress). Previously this never ran — progress was
    a manually-typed field with no auto-computation despite the signal
    scaffolding already being in place."""
    instance.project.recalculate_progress()


@receiver(post_save, sender=Portfolio)
def portfolio_post_save(sender, instance, created, **kwargs):
    """Handle portfolio post-save actions"""
    if created:
        pass


@receiver(post_delete, sender=Portfolio)
def portfolio_post_delete(sender, instance, **kwargs):
    """Handle portfolio post-delete cleanup"""
    pass
