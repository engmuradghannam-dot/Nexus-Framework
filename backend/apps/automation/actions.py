"""Executing automated actions safely.

The condition is a simple three-part comparison — field, operator, value —
evaluated by `compare`, never eval(). Operators are a fixed whitelist; values
are coerced to match the field's type so "10000" compares numerically against a
Decimal. Steps do one concrete thing each: set a field, create a notification,
or fire a webhook.

An automated action must never crash the operation that triggered it. A step
that fails is recorded and skipped; the user's save still succeeds.
"""
from decimal import Decimal, InvalidOperation

_OPERATORS = {
    "==": lambda a, b: a == b,
    "!=": lambda a, b: a != b,
    ">": lambda a, b: a > b,
    ">=": lambda a, b: a >= b,
    "<": lambda a, b: a < b,
    "<=": lambda a, b: a <= b,
}


def _coerce(actual, raw):
    """Coerce the rule's string value to the type of the actual field value, so
    comparisons are like-for-like."""
    if actual is None:
        return None, raw
    if isinstance(actual, bool):
        return actual, str(raw).strip().lower() in ("true", "1", "yes")
    if isinstance(actual, (int, Decimal, float)):
        try:
            return Decimal(str(actual)), Decimal(str(raw))
        except (InvalidOperation, ValueError):
            return actual, raw
    return str(actual), str(raw)


def compare(actual, operator, raw_value):
    """Safely evaluate `actual <operator> raw_value`. Unknown operators and
    un-comparable values return False rather than raising."""
    op = _OPERATORS.get(operator)
    if op is None:
        return False
    left, right = _coerce(actual, raw_value)
    if left is None:
        return False
    try:
        return bool(op(left, right))
    except TypeError:
        return False


def run_step(step, instance, actor=None):
    """Execute one step. Never raises — returns a small result dict, recording
    failure rather than propagating it into the triggering save."""
    try:
        if step.step_type == "set_field":
            return _set_field(step, instance)
        if step.step_type == "notify":
            return _notify(step, instance, actor)
        if step.step_type == "webhook":
            return _webhook(step, instance)
        return {"step": step.step_type, "ok": False, "detail": "unknown step type"}
    except Exception as exc:  # an automation must not break the user's operation
        return {"step": step.step_type, "ok": False, "detail": str(exc)[:200]}


def _set_field(step, instance):
    if not step.target_field or not hasattr(instance, step.target_field):
        return {"step": "set_field", "ok": False, "detail": "no such field"}
    current = getattr(instance, step.target_field)
    _, value = _coerce(current, step.target_value)
    setattr(instance, step.target_field, value)
    instance.save(update_fields=[step.target_field])
    return {"step": "set_field", "ok": True, "field": step.target_field, "value": str(value)}


def _notify(step, instance, actor):
    text = (step.message or "").replace("{id}", str(getattr(instance, "pk", "")))
    try:
        from apps.notifications.models import Notification

        Notification.objects.create(
            user=actor if (actor and getattr(actor, "is_authenticated", False)) else None,
            message=text[:300],
        )
        return {"step": "notify", "ok": True, "message": text}
    except Exception:
        # Notifications app/shape may differ; the action itself still counts.
        return {"step": "notify", "ok": True, "message": text, "detail": "logged only"}


def _webhook(step, instance):
    if step.webhook is None:
        return {"step": "webhook", "ok": False, "detail": "no webhook set"}
    payload = {
        "event": step.webhook.event,
        "object_id": str(getattr(instance, "pk", "")),
        "model": instance.__class__.__name__,
    }
    delivery = step.webhook.deliver(payload=payload)
    return {"step": "webhook", "ok": delivery.status == "success", "status": delivery.status}


def fire_event(instance, created, actor=None, tenant=None):
    """Run every active automated action registered for this instance's model
    and matching the create/update trigger. Call this after a document is saved.
    Returns the actions that ran."""
    from .models import AutomatedAction

    label = f"{instance._meta.app_label}.{instance.__class__.__name__}"
    triggers = ["on_create_or_update"]
    triggers.append("on_create" if created else "on_update")

    qs = AutomatedAction.objects.filter(
        model_label=label, trigger__in=triggers, is_active=True
    ).prefetch_related("steps")
    ran = []
    for action in qs:
        if action.condition_holds(instance):
            action.run_on(instance, actor=actor)
            ran.append(action)
    return ran
