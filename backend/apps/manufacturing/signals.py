from django.db.models.signals import post_delete, post_save
from django.dispatch import receiver

from .models import QualityInspectionParameter


@receiver(post_save, sender=QualityInspectionParameter)
@receiver(post_delete, sender=QualityInspectionParameter)
def recalc_inspection_status(sender, instance, **kwargs):
    instance.inspection.recalculate_status()
