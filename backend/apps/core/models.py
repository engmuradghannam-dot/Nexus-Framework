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
        return f"{self.name} [{self.industry_vertical.name}]"

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
        if self.capacity == 0:
            return 0
        return round((self.current_occupancy / self.capacity) * 100, 2)


# Alias for backward compatibility
Company = CompanyProfile
