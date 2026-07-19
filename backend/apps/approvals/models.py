"""Multi-level approval / release strategies.

Modelled on SAP's release strategy concept: a document doesn't get a single
yes/no, it moves through an ordered chain of release levels, each requiring a
particular role, until every level has signed off. Which strategy applies is
chosen from the document's own attributes (its type and amount), so a 500k order
routes through more levels than a 5k one without any code change — the routing
is data.

This is generic: any model can be put under a strategy by giving its content
type and primary key to an ApprovalRequest. Buying's two-signature check was a
fixed special case of this.
"""
from decimal import Decimal

from django.conf import settings
from django.contrib.contenttypes.fields import GenericForeignKey
from django.contrib.contenttypes.models import ContentType
from django.core.exceptions import ValidationError as DjangoValidationError
from django.db import models, transaction


class ReleaseStrategy(models.Model):
    """A named routing rule: which document, above what amount, needs which
    chain of approvals.

    The most specific matching strategy wins — the one with the highest
    min_amount the document reaches, for its document type. A document matching
    no strategy needs no release (it's below every threshold), which is a
    deliberate choice a company makes by where it sets its lowest strategy.
    """

    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE, null=True, blank=True, related_name="+"
    )
    name = models.CharField(max_length=120)
    document_type = models.CharField(
        max_length=60, db_index=True,
        help_text="Which document this routes, e.g. 'purchase_order'. Matches "
        "the code the caller registers the request under.",
    )
    min_amount = models.DecimalField(
        max_digits=18, decimal_places=2, default=0,
        help_text="Applies to documents whose value is at least this. Set 0 for "
        "'everything of this type'.",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["document_type", "-min_amount"]
        verbose_name_plural = "Release strategies"

    def __str__(self):
        return f"{self.name} ({self.document_type} >= {self.min_amount})"

    @classmethod
    def resolve(cls, document_type, amount, tenant=None):
        """The strategy that applies to a document of this type and amount."""
        qs = cls.objects.filter(
            document_type=document_type, is_active=True,
            min_amount__lte=Decimal(amount or 0),
        )
        if tenant is not None:
            qs = qs.filter(models.Q(tenant=tenant) | models.Q(tenant__isnull=True))
        return qs.order_by("-min_amount").first()


class ReleaseLevel(models.Model):
    """One step in a strategy's chain. Levels are released in `sequence` order;
    a level can't be released until the ones before it are."""

    strategy = models.ForeignKey(
        ReleaseStrategy, on_delete=models.CASCADE, related_name="levels"
    )
    sequence = models.PositiveSmallIntegerField(
        help_text="Order in the chain, lowest first."
    )
    role = models.ForeignKey(
        "rbac.Role", on_delete=models.PROTECT, related_name="release_levels",
        help_text="The role that must release this level.",
    )
    label = models.CharField(max_length=120, blank=True)

    class Meta:
        ordering = ["strategy", "sequence"]
        unique_together = ["strategy", "sequence"]

    def __str__(self):
        return f"{self.strategy.name} L{self.sequence} -> {self.role.name}"


class ApprovalRequest(models.Model):
    """A document placed under a release strategy, and how far it has got.

    The document is referenced generically, so nothing about the documents being
    approved needs to live here. status is derived from the steps, not set by
    hand, so it can't disagree with them.
    """

    STATUS = [
        ("pending", "Pending"),
        ("approved", "Approved"),      # every level released
        ("rejected", "Rejected"),      # any level rejected
    ]

    tenant = models.ForeignKey(
        "tenants.Tenant", on_delete=models.CASCADE, null=True, blank=True, related_name="+"
    )
    strategy = models.ForeignKey(
        ReleaseStrategy, on_delete=models.PROTECT, related_name="requests"
    )
    content_type = models.ForeignKey(ContentType, on_delete=models.CASCADE)
    object_id = models.CharField(max_length=64)
    document = GenericForeignKey("content_type", "object_id")

    document_type = models.CharField(max_length=60, db_index=True)
    amount = models.DecimalField(max_digits=18, decimal_places=2, default=0)
    requested_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="approval_requests",
    )
    status = models.CharField(max_length=10, choices=STATUS, default="pending")
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        ordering = ["-created_at"]
        indexes = [models.Index(fields=["content_type", "object_id"])]

    def __str__(self):
        return f"{self.document_type} #{self.object_id} - {self.status}"

    @classmethod
    def open_for(cls, document, document_type, amount, requested_by=None, tenant=None):
        """Place a document under approval. Builds one pending step per level of
        the resolved strategy. Returns None when no strategy applies - the
        document needs no release and the caller proceeds as before."""
        strategy = ReleaseStrategy.resolve(document_type, amount, tenant)
        if strategy is None or not strategy.levels.exists():
            return None
        ct = ContentType.objects.get_for_model(document.__class__)
        existing = cls.objects.filter(
            content_type=ct, object_id=str(document.pk), status="pending"
        ).first()
        if existing:
            return existing
        with transaction.atomic():
            req = cls.objects.create(
                tenant=tenant, strategy=strategy, content_type=ct,
                object_id=str(document.pk), document_type=document_type,
                amount=amount, requested_by=requested_by,
            )
            for level in strategy.levels.order_by("sequence"):
                ApprovalStep.objects.create(request=req, level=level)
        return req

    @property
    def current_step(self):
        """The next step awaiting action, or None if the chain is settled.

        A rejected request has no current step: a rejection at any level stops
        the chain, so the still-'pending' higher levels are moot — they'll never
        be acted on.
        """
        if self.status == "rejected":
            return None
        return ApprovalStep.objects.filter(
            request=self, decision="pending"
        ).order_by("level__sequence").select_related("level__role").first()

    def _refresh_status(self):
        # Read steps straight from the DB, not any prefetched cache on this
        # instance — the view prefetches steps at fetch time, so a cached list
        # would miss the decision we just saved.
        steps = list(ApprovalStep.objects.filter(request=self))
        if any(s.decision == "rejected" for s in steps):
            self.status = "rejected"
        elif steps and all(s.decision == "approved" for s in steps):
            self.status = "approved"
        else:
            self.status = "pending"
        self.save(update_fields=["status"])

    def act(self, user, approve=True, comment=""):
        """Approve or reject the current level.

        Enforces the chain: only the current (lowest pending) level can be
        acted on, the actor must hold that level's role, and - segregation of
        duties - the requester can never release their own document. A rejection
        stops the chain; there's no point asking higher levels once a lower one
        has said no.
        """
        from django.utils import timezone

        from apps.rbac.models import RoleAssignment

        step = self.current_step
        if step is None:
            raise DjangoValidationError("This request is already settled.")
        if self.requested_by_id and user.pk == self.requested_by_id:
            raise DjangoValidationError(
                "Segregation of duties: you cannot release a document you requested."
            )
        holds_role = RoleAssignment.objects.filter(
            user=user, role=step.level.role
        ).exists()
        if not holds_role:
            raise DjangoValidationError(
                f"This level must be released by the '{step.level.role.name}' role."
            )
        step.decision = "approved" if approve else "rejected"
        step.acted_by = user
        step.comment = comment
        step.acted_at = timezone.now()
        step.save()
        self._refresh_status()
        return self


class ApprovalStep(models.Model):
    """One level's decision on one request."""

    DECISION = [
        ("pending", "Pending"),
        ("approved", "Approved"),
        ("rejected", "Rejected"),
    ]
    request = models.ForeignKey(
        ApprovalRequest, on_delete=models.CASCADE, related_name="steps"
    )
    level = models.ForeignKey(ReleaseLevel, on_delete=models.PROTECT, related_name="+")
    decision = models.CharField(max_length=10, choices=DECISION, default="pending")
    acted_by = models.ForeignKey(
        settings.AUTH_USER_MODEL, on_delete=models.SET_NULL, null=True, blank=True,
        related_name="+",
    )
    comment = models.TextField(blank=True)
    acted_at = models.DateTimeField(null=True, blank=True)

    class Meta:
        ordering = ["request", "level__sequence"]
        unique_together = ["request", "level"]

    def __str__(self):
        return f"{self.request} L{self.level.sequence}: {self.decision}"
