"""
Generic, automatic audit trail.

Connects to every model in the business apps (not Django's own admin/auth/
session tables) and records Create/Update/Delete events with a before/after
diff, attributed to whichever user made the request (see threadlocal.py /
CompanyScopedMixin.initial / AuditUserMixin.initial for how the user gets
in here — signal handlers otherwise have no access to the request).
"""
from django.db.models.signals import pre_save, post_save, post_delete
from django.apps import apps as django_apps
from .threadlocal import get_current_user

TRACKED_APP_LABELS = {
    'core', 'accounts', 'buying', 'selling', 'inventory', 'hr',
    'assets', 'manufacturing', 'projects', 'crm', 'workflow',
}
# Low-value or self-referential — don't audit these, to avoid noise/recursion.
EXCLUDED_MODEL_NAMES = {'auditlog', 'module'}


def _tracked(model):
    return (
        model._meta.app_label in TRACKED_APP_LABELS
        and model._meta.model_name not in EXCLUDED_MODEL_NAMES
    )


def _serialize(value):
    if value is None:
        return None
    return str(value)[:200]


def _snapshot(instance):
    """Field-name -> scalar value, using attname so FKs give us the raw
    _id instead of triggering a query to fetch the related object."""
    return {f.attname: getattr(instance, f.attname, None) for f in instance._meta.fields}


def _pre_save_handler(sender, instance, **kwargs):
    if not _tracked(sender):
        return
    if not instance.pk:
        instance._audit_old_snapshot = None
        return
    try:
        instance._audit_old_snapshot = _snapshot(sender.objects.get(pk=instance.pk))
    except sender.DoesNotExist:
        instance._audit_old_snapshot = None


def _post_save_handler(sender, instance, created, **kwargs):
    if not _tracked(sender):
        return
    from .models import AuditLog

    if created:
        changes = {
            f.attname: _serialize(getattr(instance, f.attname, None))
            for f in instance._meta.fields
            if getattr(instance, f.attname, None) not in (None, '', 0)
        }
        action = 'Create'
    else:
        old = getattr(instance, '_audit_old_snapshot', None) or {}
        new = _snapshot(instance)
        changes = {
            attname: [_serialize(old.get(attname)), _serialize(new_val)]
            for attname, new_val in new.items()
            if old.get(attname) != new_val
        }
        if not changes:
            return  # save() called but nothing actually changed — skip the noise
        action = 'Update'

    AuditLog.objects.create(
        user=get_current_user(), action=action,
        app_label=sender._meta.app_label, model_name=sender._meta.model_name,
        object_id=str(instance.pk), object_repr=str(instance)[:255], changes=changes,
    )


def _post_delete_handler(sender, instance, **kwargs):
    if not _tracked(sender):
        return
    from .models import AuditLog
    AuditLog.objects.create(
        user=get_current_user(), action='Delete',
        app_label=sender._meta.app_label, model_name=sender._meta.model_name,
        object_id=str(instance.pk), object_repr=str(instance)[:255], changes={},
    )


def connect_signals():
    for model in django_apps.get_models():
        if not _tracked(model):
            continue
        pre_save.connect(_pre_save_handler, sender=model, weak=False)
        post_save.connect(_post_save_handler, sender=model, weak=False)
        post_delete.connect(_post_delete_handler, sender=model, weak=False)
