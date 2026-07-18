"""Project-wide DRF exception handling.

Deleting a record that financial history points at (an item with stock
movements, an account with journal lines) now raises Django's ProtectedError,
which DRF doesn't understand and would surface as a 500. That's the right
outcome — the delete must not proceed — but the wrong presentation: the caller
deserves a clear 'you can't delete this and here's why', not a server error.
"""
from django.db.models import ProtectedError
from rest_framework import status
from rest_framework.response import Response
from rest_framework.views import exception_handler as drf_exception_handler


def exception_handler(exc, context):
    if isinstance(exc, ProtectedError):
        protected = getattr(exc, "protected_objects", [])
        sample = ", ".join(str(o) for o in list(protected)[:3])
        more = "" if len(list(protected)) <= 3 else f" (+{len(list(protected)) - 3} more)"
        return Response(
            {
                "detail": (
                    "This record is referenced by other records that depend on it "
                    "and cannot be deleted. Referenced by: "
                    f"{sample}{more}."
                )
            },
            status=status.HTTP_409_CONFLICT,
        )
    return drf_exception_handler(exc, context)
