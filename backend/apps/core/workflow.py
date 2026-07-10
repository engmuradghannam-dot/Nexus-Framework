"""Workflow / state-machine helpers for the Nexus Framework.

Provides a small, dependency-free state-transition validator and a helper
for running status-change side effects atomically. Both are consumed by the
serializers of every business app (selling, buying, inventory, accounts,
manufacturing, hr, assets).
"""

from django.db import transaction
from rest_framework import serializers


def validate_transition(transitions, current_status, new_status):
    """Validate that a status change is allowed by a transition map.

    ``transitions`` is a dict mapping each status to the set (or iterable) of
    statuses it may move to, e.g.::

        {'Draft': {'Submitted', 'Cancelled'}, 'Submitted': {'Delivered'}}

    Raises ``rest_framework.serializers.ValidationError`` when the move is not
    permitted, so DRF surfaces it as a clean HTTP 400.
    """
    if current_status == new_status:
        return new_status

    allowed = transitions.get(current_status)
    if allowed is None:
        raise serializers.ValidationError(
            {"status": f"Unknown status '{current_status}'."}
        )
    if new_status not in allowed:
        allowed_list = ", ".join(sorted(allowed)) if allowed else "none"
        raise serializers.ValidationError(
            {
                "status": (
                    f"Invalid transition from '{current_status}' to "
                    f"'{new_status}'. Allowed: {allowed_list}."
                )
            }
        )
    return new_status


def run_side_effect(func, *args, **kwargs):
    """Run a status-change side effect (e.g. posting stock) atomically.

    Executes ``func(*args, **kwargs)`` inside a database transaction so that a
    failure rolls back cleanly. Any error raised by the side effect is
    re-surfaced as a DRF ``ValidationError`` to keep the API response clean.
    """
    try:
        with transaction.atomic():
            return func(*args, **kwargs)
    except serializers.ValidationError:
        raise
    except Exception as exc:  # noqa: BLE001 - surface any side-effect failure
        raise serializers.ValidationError(
            {"detail": f"Operation failed: {exc}"}
        ) from exc
