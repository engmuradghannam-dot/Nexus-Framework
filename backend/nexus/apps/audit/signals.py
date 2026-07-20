from contextvars import ContextVar
from decimal import Decimal, InvalidOperation

from django.db import models as django_models

_current_user: ContextVar = ContextVar('current_audit_user', default=None)
_PRE_SAVE_SNAPSHOT_ATTR = '_audit_pre_save_snapshot'

# model -> iterable of field names to track, or None to track every field
_AUDITED_MODELS = {}


def set_current_audit_user(user):
    _current_user.set(user)


def get_current_audit_user():
    return _current_user.get()


def register_audited_model(model, fields=None):
    _AUDITED_MODELS[model] = fields


def _normalize(field, value):
    """Freshly-assigned (not yet DB round-tripped) field values may be plain
    ints/floats rather than properly-scaled Decimals - normalize so old/new
    values compare and print consistently regardless of source."""
    if value is None or not isinstance(field, django_models.DecimalField):
        return value
    try:
        return Decimal(value).quantize(Decimal(1).scaleb(-field.decimal_places))
    except (InvalidOperation, TypeError, ValueError):
        return value


def _snapshot(instance, tracked_fields=None):
    data = {}
    for f in instance._meta.fields:
        if tracked_fields and f.name not in tracked_fields:
            continue
        value = getattr(instance, f.attname if f.is_relation else f.name)
        data[f.name] = _normalize(f, value)
    return data


def _actor():
    user = get_current_audit_user()
    if user and getattr(user, 'is_authenticated', False):
        return user, user.username
    return None, 'system'


def _pre_save_handler(sender, instance, **kwargs):
    if sender not in _AUDITED_MODELS or not instance.pk:
        return
    try:
        old = sender.objects.get(pk=instance.pk)
    except sender.DoesNotExist:
        return
    setattr(instance, _PRE_SAVE_SNAPSHOT_ATTR, _snapshot(old, _AUDITED_MODELS[sender]))


def _write_header(sender, instance, change_type):
    from django.contrib.contenttypes.models import ContentType

    from .models import ChangeHeader

    user, username = _actor()
    content_type = ContentType.objects.get_for_model(sender)
    return ChangeHeader.objects.create(
        content_type=content_type,
        object_id=str(instance.pk),
        object_repr=str(instance)[:200],
        change_type=change_type,
        changed_by=user,
        username_snapshot=username,
    )


def _post_save_handler(sender, instance, created, **kwargs):
    if sender not in _AUDITED_MODELS:
        return
    from .models import ChangeItem

    tracked_fields = _AUDITED_MODELS[sender]
    new_values = _snapshot(instance, tracked_fields)

    if created:
        header = _write_header(sender, instance, 'I')
        items = [
            ChangeItem(header=header, field_name=k, change_indicator='I', value_old='', value_new=str(v)[:1000])
            for k, v in new_values.items() if v not in (None, '')
        ]
        if items:
            ChangeItem.objects.bulk_create(items)
        return

    old_values = getattr(instance, _PRE_SAVE_SNAPSHOT_ATTR, None)
    if old_values is None:
        return
    changed = [(k, old_values.get(k), v) for k, v in new_values.items() if old_values.get(k) != v]
    if not changed:
        return
    header = _write_header(sender, instance, 'U')
    ChangeItem.objects.bulk_create([
        ChangeItem(
            header=header, field_name=k, change_indicator='U',
            value_old='' if o is None else str(o)[:1000],
            value_new='' if n is None else str(n)[:1000],
        )
        for k, o, n in changed
    ])


def _post_delete_handler(sender, instance, **kwargs):
    if sender not in _AUDITED_MODELS:
        return
    from .models import ChangeItem

    header = _write_header(sender, instance, 'D')
    values = _snapshot(instance, _AUDITED_MODELS[sender])
    ChangeItem.objects.bulk_create([
        ChangeItem(header=header, field_name=k, change_indicator='D', value_old='' if v is None else str(v)[:1000], value_new='')
        for k, v in values.items()
    ])


def connect_signals():
    from django.db.models.signals import post_delete, post_save, pre_save

    pre_save.connect(_pre_save_handler, dispatch_uid='audit_pre_save')
    post_save.connect(_post_save_handler, dispatch_uid='audit_post_save')
    post_delete.connect(_post_delete_handler, dispatch_uid='audit_post_delete')
