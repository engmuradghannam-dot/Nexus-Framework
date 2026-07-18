from django.core.exceptions import ValidationError
import uuid

from django.contrib.auth.models import AbstractUser, BaseUserManager
from django.db import models


class UserManager(BaseUserManager):
    """Email-based manager for the custom User (USERNAME_FIELD = 'email').

    Accepts email/username/password positionally or by keyword so all existing
    call sites keep working; username defaults to the email when omitted.
    """

    def _create_user(self, email=None, username=None, password=None, **extra_fields):
        if not email:
            raise ValueError("Users must have an email address")
        email = self.normalize_email(email)
        if not username:
            username = email
        user = self.model(email=email, username=username, **extra_fields)
        user.set_password(password)
        user.save(using=self._db)
        return user

    def create_user(self, email=None, username=None, password=None, **extra_fields):
        extra_fields.setdefault("is_staff", False)
        extra_fields.setdefault("is_superuser", False)
        return self._create_user(email, username, password, **extra_fields)

    def create_superuser(
        self, email=None, username=None, password=None, **extra_fields
    ):
        extra_fields.setdefault("is_staff", True)
        extra_fields.setdefault("is_superuser", True)
        if extra_fields.get("is_staff") is not True:
            raise ValueError("Superuser must have is_staff=True.")
        if extra_fields.get("is_superuser") is not True:
            raise ValueError("Superuser must have is_superuser=True.")
        return self._create_user(email, username, password, **extra_fields)


class User(AbstractUser):
    """Extended user with role-based permissions linked to HR."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    department = models.CharField(max_length=100, blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    avatar = models.ImageField(upload_to="avatars/", blank=True, null=True)
    is_department_head = models.BooleanField(default=False)
    tenant = models.ForeignKey("tenants.Tenant", on_delete=models.SET_NULL, null=True, blank=True, related_name="users")
    permissions_level = models.PositiveSmallIntegerField(
        choices=[
            (1, "Viewer"),
            (2, "Editor"),
            (3, "Manager"),
            (4, "Admin"),
            (5, "Superuser"),
        ],
        default=1,
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    objects = UserManager()

    USERNAME_FIELD = "email"
    REQUIRED_FIELDS = ["username"]

    class Meta:
        db_table = "core_users"
        ordering = ["-created_at"]

    def __str__(self):
        return f"{self.email} ({self.get_permissions_level_display()})"


class CompanyProfile(models.Model):
    """
    Company Profile - links to Industry Vertical.
    This is the ROOT entity that determines what modules/features are available.

    NOT the same model as ``apps.industry.models.Company``:
    - ``core.CompanyProfile`` (this model) is the Nexus TENANT itself — the
      organisation that owns the data (branches, warehouses, users) in this
      installation. Referenced by ``core.Branch``, ``core.Warehouse``, etc.
    - ``industry.Company`` is a record TRACKED by the Industry Intelligence
      module (e.g. a portfolio/competitor company being analysed) — it has
      market cap, revenue, employee count, and industry metrics, and is
      unrelated to who owns this Nexus tenant.
    The similar naming is a known source of confusion (see the
    "تقرير_مراجعة" review, P2 #5); the two are kept separate deliberately
    rather than merged, since merging would conflate "who runs Nexus" with
    "what Nexus is analysing".
    """

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200, unique=True)
    code = models.CharField(max_length=20, unique=True)

    # Industry Vertical is the PARENT - it CONTROLS everything
    industry_vertical = models.ForeignKey(
        "industry.IndustryVertical",
        on_delete=models.PROTECT,
        related_name="company_profiles",
        null=True,
        blank=True,
        help_text="The Industry Vertical that controls this company's modules and features",
    )

    # Super Admin who configured this company
    super_admin = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_companies",
    )

    # Company settings derived from vertical (can override)
    currency = models.CharField(max_length=3, default="USD")
    timezone = models.CharField(max_length=50, default="UTC")

    # Feature toggles derived from Industry Vertical
    modules_enabled = models.JSONField(
        default=list, blank=True, help_text="Override vertical modules"
    )
    features_enabled = models.JSONField(
        default=dict, blank=True, help_text="Override vertical features"
    )

    # Multi-branch/warehouse
    multi_branch_enabled = models.BooleanField(default=False)
    multi_warehouse_enabled = models.BooleanField(default=False)

    # Company info
    logo = models.ImageField(upload_to="company_logos/", blank=True, null=True)
    address = models.TextField(blank=True)
    phone = models.CharField(max_length=30, blank=True)
    email = models.EmailField(blank=True)
    website = models.URLField(blank=True)

    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        db_table = "core_company_profiles"
        ordering = ["name"]
        verbose_name = "Company Profile"
        verbose_name_plural = "Company Profiles"

    def __str__(self):
        # industry_vertical is nullable, so the old unconditional
        # `self.industry_vertical.name` raised AttributeError for any company
        # without one — in admin lists, error messages, and anywhere a company
        # gets interpolated into a string.
        if self.industry_vertical_id:
            return f"{self.name} [{self.industry_vertical.name}]"
        return self.name

    @property
    def effective_modules(self):
        """Return all enabled modules (vertical + company override)"""
        base = set(self.industry_vertical.modules_enabled)
        custom = set(self.modules_enabled)
        return sorted(list(base | custom))

    @property
    def effective_features(self):
        """Return all enabled features (vertical + company override)"""
        base = self.industry_vertical.features_config.copy()
        custom = self.features_enabled
        for module, features in custom.items():
            if module in base:
                base[module] = list(set(base[module] + features))
            else:
                base[module] = features
        return base


class Branch(models.Model):
    BRANCH_TYPES = [
        ("Head Office", "Head Office"),
        ("Branch", "Branch"),
        ("Warehouse", "Warehouse"),
        ("Showroom", "Showroom"),
    ]

    """Company branches with Google Maps location."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    company = models.ForeignKey(
        CompanyProfile,
        on_delete=models.CASCADE,
        related_name="branches",
        null=True,
        blank=True,
    )
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    address = models.TextField()
    latitude = models.DecimalField(
        max_digits=10, decimal_places=7, null=True, blank=True
    )
    longitude = models.DecimalField(
        max_digits=10, decimal_places=7, null=True, blank=True
    )
    phone = models.CharField(max_length=30, blank=True)
    manager = models.ForeignKey(
        User,
        on_delete=models.SET_NULL,
        null=True,
        blank=True,
        related_name="managed_branches",
    )
    branch_type = models.CharField(
        max_length=50, choices=BRANCH_TYPES, default="Branch",
        help_text="BRN-RULE-002: only one Head Office is allowed per company.",
    )
    open_time = models.TimeField(null=True, blank=True)
    close_time = models.TimeField(null=True, blank=True)
    license_number = models.CharField(max_length=100, blank=True)
    license_expiry = models.DateField(
        null=True, blank=True,
        help_text="BRN-CTRL-005: commercial license expiry, alerted on 60 days ahead.",
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "core_branches"
        ordering = ["name"]

    def __str__(self):
        return self.name

    def profit_and_loss(self, start_date, end_date):
        """BRN-CTRL-004: income, expense and net for this branch over a period.

        Derived from journal entries tagged with the branch. JournalEntry.branch
        already existed but nothing ever populated it, so a per-branch P&L would
        have reported zero for every branch forever. Entries with no branch
        (anything posted before the tag was filled, or from a source with no
        branch of its own) are excluded rather than spread around — inventing an
        allocation would be worse than showing what is actually attributable.
        """
        from decimal import Decimal

        from django.db.models import Q, Sum

        from apps.accounts.models import JournalEntry

        entries = JournalEntry.objects.filter(
            branch=self, posting_date__range=(start_date, end_date),
        ).exclude(status="Cancelled")

        def total(account_type, side):
            field = f"{side}_account"
            return entries.filter(
                **{f"{field}__account_type": account_type}
            ).aggregate(t=Sum("amount"))["t"] or Decimal(0)

        # Income is earned when credited; expense is incurred when debited.
        income = total("Income", "credit") - total("Income", "debit")
        expense = total("Expense", "debit") - total("Expense", "credit")
        return {
            "branch": self.name,
            "start_date": start_date,
            "end_date": end_date,
            "income": income,
            "expense": expense,
            "net_profit": income - expense,
            "entries": entries.count(),
        }

    def clean(self):
        """BRN-RULE-002 (one Head Office per company) and BRN-RULE-005
        (close time must be after open time)."""
        from django.core.exceptions import ValidationError

        if self.branch_type == "Head Office":
            clash = Branch.objects.filter(
                company=self.company, branch_type="Head Office"
            ).exclude(pk=self.pk)
            if clash.exists():
                raise ValidationError(
                    {"branch_type": "هذه الشركة لديها مقر رئيسي بالفعل / "
                                    "Head Office already exists for this company"}
                )
        if self.open_time and self.close_time and self.close_time <= self.open_time:
            raise ValidationError(
                {"close_time": "وقت الإغلاق يجب أن يكون بعد وقت الفتح / "
                               "Close time must be after open time"}
            )

    def save(self, *args, **kwargs):
        # Only the two Branch business rules — not full_clean(), which would
        # also re-run every field/uniqueness validator on every save and can
        # reject rows that were acceptable before these rules existed.
        self.clean()
        super().save(*args, **kwargs)

    def distance_to(self, other):
        """BRN-RULE-004: great-circle distance in km to another branch
        (Haversine). Returns None unless both branches have coordinates."""
        from math import asin, cos, radians, sin, sqrt

        if None in (self.latitude, self.longitude, other.latitude, other.longitude):
            return None
        lat1, lon1, lat2, lon2 = map(
            radians,
            [float(self.latitude), float(self.longitude),
             float(other.latitude), float(other.longitude)],
        )
        dlat, dlon = lat2 - lat1, lon2 - lon1
        a = sin(dlat / 2) ** 2 + cos(lat1) * cos(lat2) * sin(dlon / 2) ** 2
        return round(2 * asin(sqrt(a)) * 6371.0088, 2)

    @property
    def license_expires_soon(self):
        """BRN-CTRL-005: True within 60 days of commercial-license expiry."""
        from datetime import date, timedelta

        if not self.license_expiry:
            return False
        return self.license_expiry <= date.today() + timedelta(days=60)


class Warehouse(models.Model):
    """Branch warehouses / sub-warehouses."""

    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    branch = models.ForeignKey(
        Branch, on_delete=models.CASCADE, related_name="warehouses"
    )
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    parent_warehouse = models.ForeignKey(
        "self",
        on_delete=models.CASCADE,
        null=True,
        blank=True,
        related_name="sub_warehouses",
    )
    capacity = models.PositiveIntegerField(default=0, help_text="Max items")
    current_occupancy = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "core_warehouses"
        ordering = ["branch__name", "name"]

    def __str__(self):
        return f"{self.name} ({self.branch.name})"

    @property
    def occupancy_rate(self):
        """Percentage of capacity actually consumed by stock on hand.

        This used to divide by ``current_occupancy`` — a hand-entered field that
        nothing in the system ever wrote to, so the rate (and every alert built
        on it) reported whatever someone last typed. It now derives from stock
        entries, which is what WHS-RULE-004 and WHS-CTRL-002 need to mean
        anything.
        """
        if not self.capacity:
            return 0
        return round((float(self.stock_units) / self.capacity) * 100, 2)

    @property
    def stock_units(self):
        """Units on hand in this warehouse, from the stock ledger."""
        from decimal import Decimal

        from django.db.models import Case, DecimalField, F, Sum, When

        from django.db.models import Q

        from apps.inventory.models import StockEntry

        agg = StockEntry.objects.filter(
            Q(warehouse=self) | Q(source_warehouse=self) | Q(target_warehouse=self)
        ).aggregate(
            qty=Sum(
                Case(
                    When(entry_type="Receipt", warehouse=self, then="quantity"),
                    When(entry_type="Issue", warehouse=self, then=-F("quantity")),
                    When(entry_type="Transfer", target_warehouse=self, then="quantity"),
                    When(entry_type="Transfer", source_warehouse=self, then=-F("quantity")),
                    default=Decimal(0),
                    output_field=DecimalField(max_digits=18, decimal_places=2),
                )
            )
        )
        return agg["qty"] or Decimal(0)

    @property
    def is_near_capacity(self):
        """WHS-CTRL-002: warehouse has reached 90% of capacity."""
        return bool(self.capacity) and self.occupancy_rate >= 90

    @property
    def uses_bins(self):
        """WHS-CTRL-001 only bites for warehouses that have defined bins, so
        existing single-location warehouses are unaffected."""
        return self.bins.filter(is_active=True).exists()

    def suggest_putaway_bin(self, item, qty):
        """WHS-RULE-001: pick the best bin for an incoming quantity.

        Preference order, per the spec's "product category and turnover":
        1. an active bin dedicated to the item's group that can hold the qty,
           closest to the front of the pick route (fast-moving stock should not
           be at the back of the walk);
        2. otherwise any general-purpose bin that can hold it.
        Returns None when the warehouse has no bins or none can take the qty.
        """
        candidates = self.bins.filter(is_active=True).order_by("pick_sequence", "code")
        dedicated = [
            b for b in candidates if b.item_group_id and b.item_group_id == item.item_group_id
        ]
        general = [b for b in candidates if not b.item_group_id]
        for bucket in (dedicated, general):
            for b in bucket:
                if b.can_hold(qty):
                    return b
        return None

    def pick_route(self, lines):
        """WHS-RULE-002: order pick lines by zone proximity (wave picking).

        `lines` is an iterable of (item, qty). Returns a list of
        (bin, item, qty) sorted by the bins' pick_sequence so the picker walks
        the warehouse once instead of criss-crossing it. Items with no stock in
        any bin come back with bin=None rather than being silently dropped —
        the picker still needs to know they were asked for.
        """
        route = []
        for item, qty in lines:
            entries = (
                item.stockentry_set.filter(warehouse=self, bin_location__isnull=False)
                .select_related("bin_location")
                .order_by("bin_location__pick_sequence")
            )
            chosen = None
            for e in entries:
                if e.bin_location.stock_units > 0:
                    chosen = e.bin_location
                    break
            route.append((chosen, item, qty))
        return sorted(
            route,
            key=lambda r: (r[0] is None, r[0].pick_sequence if r[0] else 0),
        )

    def check_capacity(self, additional_units):
        """WHS-RULE-004: refuse a movement that would overfill the warehouse.

        A capacity of 0 means "not configured" and is not enforced, so
        warehouses that predate this rule keep working until a capacity is set.
        """
        from decimal import Decimal

        from django.core.exceptions import ValidationError

        if not self.capacity:
            return
        projected = self.stock_units + Decimal(additional_units or 0)
        if projected > self.capacity:
            raise ValidationError(
                f"Zone capacity exceeded for {self.name}: {projected} units would "
                f"exceed capacity {self.capacity}."
            )


# Alias for backward compatibility
Company = CompanyProfile


class BinLocation(models.Model):
    """A storage position inside a warehouse — zone / aisle / rack / bin.

    WHS-CTRL-001 requires every item to have a bin/rack location, and
    WHS-RULE-001 (putaway) and WHS-RULE-002 (pick sequence) both need somewhere
    to route to and a traversal order to route by. Warehouses without any bins
    keep working exactly as before: bins are opt-in per warehouse.
    """

    warehouse = models.ForeignKey(
        "Warehouse", on_delete=models.CASCADE, related_name="bins"
    )
    code = models.CharField(max_length=50)
    zone = models.CharField(max_length=50, blank=True)
    aisle = models.CharField(max_length=50, blank=True)
    rack = models.CharField(max_length=50, blank=True)
    item_group = models.ForeignKey(
        "inventory.ItemGroup", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="bins",
        help_text="WHS-RULE-001: putaway prefers a bin dedicated to the item's group.",
    )
    capacity = models.PositiveIntegerField(
        default=0, help_text="Units this bin holds. 0 means unconstrained."
    )
    pick_sequence = models.PositiveIntegerField(
        default=0,
        help_text="WHS-RULE-002: traversal order for wave picking — lower is "
        "reached first on the walk route.",
    )
    is_active = models.BooleanField(default=True)

    class Meta:
        db_table = "core_bin_locations"
        ordering = ["warehouse", "pick_sequence", "code"]
        constraints = [
            models.UniqueConstraint(
                fields=["warehouse", "code"], name="unique_bin_code_per_warehouse"
            )
        ]

    def __str__(self):
        return f"{self.warehouse.code}/{self.code}"

    @property
    def stock_units(self):
        from decimal import Decimal

        from django.db.models import Case, DecimalField, F, Sum, When

        agg = self.stock_entries.aggregate(
            qty=Sum(
                Case(
                    When(entry_type="Receipt", then="quantity"),
                    When(entry_type="Issue", then=-F("quantity")),
                    default=Decimal(0),
                    output_field=DecimalField(max_digits=18, decimal_places=2),
                )
            )
        )
        return agg["qty"] or Decimal(0)

    @property
    def free_capacity(self):
        from decimal import Decimal

        if not self.capacity:
            return None  # unconstrained
        return Decimal(self.capacity) - self.stock_units

    def can_hold(self, qty):
        from decimal import Decimal

        free = self.free_capacity
        return free is None or free >= Decimal(qty)


class CycleCount(models.Model):
    """WHS-CTRL-003: a monthly spot-check of one zone.

    Distinct from StockReconciliation, which is a full count of a warehouse.
    A cycle count samples a zone so discrepancies surface between full counts
    instead of at year end.
    """

    STATUS_CHOICES = [
        ("Scheduled", "Scheduled"),
        ("Counted", "Counted"),
        ("Reconciled", "Reconciled"),
        ("Cancelled", "Cancelled"),
    ]
    warehouse = models.ForeignKey(
        "Warehouse", on_delete=models.CASCADE, related_name="cycle_counts"
    )
    zone = models.CharField(max_length=50, blank=True)
    scheduled_date = models.DateField()
    counted_by = models.ForeignKey(
        "hr.Employee", on_delete=models.SET_NULL, null=True, blank=True,
        related_name="cycle_counts",
    )
    status = models.CharField(max_length=50, choices=STATUS_CHOICES, default="Scheduled")
    notes = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = "core_cycle_counts"
        ordering = ["-scheduled_date", "-id"]

    def __str__(self):
        return f"Cycle count {self.warehouse.code}/{self.zone or 'all'} {self.scheduled_date}"

    @classmethod
    def generate(cls, warehouse, zone, scheduled_date, sample_size=5):
        """Draw a random sample of items held in a zone.

        Random per the spec: a fixed list would let anyone with something to
        hide learn which items are never checked.
        """
        import random

        from apps.inventory.models import Item, StockEntry

        entries = StockEntry.objects.filter(warehouse=warehouse)
        if zone:
            entries = entries.filter(bin_location__zone=zone)
        item_ids = list(entries.values_list("item_id", flat=True).distinct())
        if not item_ids:
            raise ValidationError(
                f"No stock recorded in zone '{zone or 'all'}' of {warehouse.name}."
            )
        chosen = random.sample(item_ids, min(sample_size, len(item_ids)))
        count = cls.objects.create(
            warehouse=warehouse, zone=zone, scheduled_date=scheduled_date
        )
        for item in Item.objects.filter(pk__in=chosen):
            CycleCountLine.objects.create(
                cycle_count=count, item=item,
                system_qty=item.stock_in_warehouse(warehouse),
            )
        return count

    @property
    def total_variance(self):
        from decimal import Decimal

        return sum((line.variance for line in self.lines.all()), Decimal(0))

    @property
    def has_discrepancy(self):
        return any(line.variance != 0 for line in self.lines.all())

    def reconcile(self):
        """Post the difference so the ledger matches what was actually counted."""
        from decimal import Decimal

        from django.db import transaction as db_transaction

        from apps.inventory.models import StockEntry

        if self.status != "Counted":
            raise ValidationError(
                f"Only a counted cycle count can be reconciled (this one is "
                f"'{self.status}')."
            )
        lines = list(self.lines.select_related("item"))
        with db_transaction.atomic():
            for line in lines:
                if line.counted_qty is None or line.variance == 0:
                    continue
                StockEntry.objects.create(
                    company=self.warehouse.branch.company,
                    branch=self.warehouse.branch,
                    warehouse=self.warehouse,
                    item=line.item,
                    entry_type="Receipt" if line.variance > 0 else "Issue",
                    quantity=abs(line.variance),
                    rate=line.item.valuation_rate(self.warehouse) or Decimal(0),
                    reference=f"Cycle count {self.pk} adjustment",
                )
            self.status = "Reconciled"
            self.save(update_fields=["status"])
        return True, "تمت تسوية الجرد / Cycle count reconciled"


class CycleCountLine(models.Model):
    cycle_count = models.ForeignKey(
        CycleCount, on_delete=models.CASCADE, related_name="lines"
    )
    item = models.ForeignKey("inventory.Item", on_delete=models.CASCADE)
    system_qty = models.DecimalField(
        max_digits=18, decimal_places=2, default=0,
        help_text="What the system believed at the moment the count was drawn.",
    )
    counted_qty = models.DecimalField(
        max_digits=18, decimal_places=2, null=True, blank=True,
        help_text="Null until someone actually counts it.",
    )

    class Meta:
        db_table = "core_cycle_count_lines"
        ordering = ["id"]

    @property
    def variance(self):
        from decimal import Decimal

        if self.counted_qty is None:
            return Decimal(0)
        return Decimal(self.counted_qty) - Decimal(self.system_qty)
