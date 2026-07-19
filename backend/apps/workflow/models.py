"""A lightweight BPM / workflow engine — state machines for documents.

A Workflow is a named set of States connected by Transitions. Any document can
be attached to a workflow as a WorkflowInstance, which sits in one state at a
time and moves along defined transitions. A transition can require a role, so
who may move a document from 'submitted' to 'approved' is data, not code.

This is more general than the approval chain: approvals are a linear release
ladder, whereas a workflow is an arbitrary graph — branches, loops back, parallel
paths modelled as separate transitions out of one state. Approvals answer 'is
this released?'; a workflow answers 'where in its lifecycle is this, and where
can it go next?'.
"""
from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import models


class Workflow(models.Model):
    """A named lifecycle for a kind of document."""

    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE, null=True, blank=True, related_name="+"
    )
    name = models.CharField(max_length=150)
    document_type = models.CharField(
        max_length=60, db_index=True,
        help_text="Which documents this governs, e.g. 'purchase_order'.",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["name"]

    def __str__(self):
        return self.name

    @property
    def initial_state(self):
        return self.states.filter(is_initial=True).order_by("id").first()


class State(models.Model):
    """One node in a workflow — a place a document can be."""

    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name="states")
    key = models.CharField(max_length=40, help_text="Stable code, e.g. 'draft'.")
    label = models.CharField(max_length=120)
    label_ar = models.CharField(max_length=120, blank=True)
    is_initial = models.BooleanField(default=False)
    is_final = models.BooleanField(default=False)

    class Meta:
        ordering = ["workflow", "id"]
        unique_together = ["workflow", "key"]

    def __str__(self):
        return f"{self.workflow.name}:{self.key}"


class Transition(models.Model):
    """A permitted move from one state to another, optionally gated by a role."""

    workflow = models.ForeignKey(Workflow, on_delete=models.CASCADE, related_name="transitions")
    name = models.CharField(max_length=120, help_text="The action, e.g. 'Submit'.")
    from_state = models.ForeignKey(State, on_delete=models.CASCADE, related_name="outgoing")
    to_state = models.ForeignKey(State, on_delete=models.CASCADE, related_name="incoming")
    required_role = models.ForeignKey(
        "rbac.Role", on_delete=models.PROTECT, null=True, blank=True, related_name="+",
        help_text="If set, only a user with this role may take this transition.",
    )

    class Meta:
        ordering = ["workflow", "id"]
        unique_together = ["workflow", "from_state", "to_state", "name"]

    def __str__(self):
        return f"{self.name}: {self.from_state.key} → {self.to_state.key}"


class WorkflowInstance(models.Model):
    """A document travelling through a workflow — where it is right now."""

    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE, null=True, blank=True, related_name="+"
    )
    workflow = models.ForeignKey(Workflow, on_delete=models.PROTECT, related_name="instances")
    current_state = models.ForeignKey(State, on_delete=models.PROTECT, related_name="+")

    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=64)
    document = GenericForeignKey("content_type", "object_id")

    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        ordering = ["-updated_at"]
        indexes = [models.Index(fields=["content_type", "object_id"])]

    def __str__(self):
        return f"{self.workflow.name} @ {self.current_state.key}"

    @classmethod
    def start(cls, workflow, document, tenant=None):
        """Attach a document to a workflow at its initial state. Returns the
        existing instance if one already exists for this document."""
        initial = workflow.initial_state
        if initial is None:
            raise DjangoValidationError("Workflow has no initial state.")
        ct = ContentType.objects.get_for_model(document.__class__)
        existing = cls.objects.filter(content_type=ct, object_id=str(document.pk)).first()
        if existing:
            return existing
        return cls.objects.create(
            tenant=tenant, workflow=workflow, current_state=initial,
            content_type=ct, object_id=str(document.pk),
        )

    def available_transitions(self, user=None):
        """Transitions out of the current state, optionally filtered to those
        the user is allowed to take."""
        qs = Transition.objects.filter(
            workflow=self.workflow, from_state=self.current_state
        ).select_related("to_state", "required_role")
        if user is None:
            return list(qs)
        from apps.rbac.models import RoleAssignment

        roles = set(RoleAssignment.objects.filter(user=user).values_list("role_id", flat=True))
        return [t for t in qs if t.required_role_id is None or t.required_role_id in roles]

    def can_take(self, transition, user):
        if transition.from_state_id != self.current_state_id:
            return False, "That transition doesn't start from the current state."
        if transition.required_role_id:
            from apps.rbac.models import RoleAssignment

            if not RoleAssignment.objects.filter(
                user=user, role_id=transition.required_role_id
            ).exists():
                return False, f"This transition requires the '{transition.required_role.name}' role."
        return True, ""

    def take(self, transition, user, note=""):
        """Move the document along a transition, recording the history entry."""
        ok, reason = self.can_take(transition, user)
        if not ok:
            raise DjangoValidationError(reason)
        from_state = self.current_state
        self.current_state = transition.to_state
        self.save(update_fields=["current_state", "updated_at"])
        WorkflowHistory.objects.create(
            instance=self, transition=transition,
            from_state=from_state, to_state=transition.to_state,
            actor=user if (user and getattr(user, "is_authenticated", False)) else None,
            note=note,
        )
        return self


class WorkflowHistory(models.Model):
    """An immutable record of one move a document made through its workflow."""

    instance = models.ForeignKey(
        WorkflowInstance, on_delete=models.CASCADE, related_name="history"
    )
    transition = models.ForeignKey(Transition, on_delete=models.SET_NULL, null=True, related_name="+")
    from_state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True, related_name="+")
    to_state = models.ForeignKey(State, on_delete=models.SET_NULL, null=True, related_name="+")
    actor = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True, related_name="+"
    )
    note = models.TextField(blank=True)
    timestamp = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["instance", "timestamp"]
        verbose_name_plural = "Workflow history"

    def __str__(self):
        return f"{self.from_state} → {self.to_state}"
