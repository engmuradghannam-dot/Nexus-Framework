from django.db import models
from django.contrib.auth.models import AbstractUser
import uuid


class User(AbstractUser):
    """Extended user with role-based permissions linked to HR."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    email = models.EmailField(unique=True)
    department = models.CharField(max_length=100, blank=True)
    job_title = models.CharField(max_length=100, blank=True)
    avatar = models.ImageField(upload_to='avatars/', blank=True, null=True)
    is_department_head = models.BooleanField(default=False)
    permissions_level = models.PositiveSmallIntegerField(
        choices=[
            (1, 'Viewer'),
            (2, 'Editor'),
            (3, 'Manager'),
            (4, 'Admin'),
            (5, 'Superuser'),
        ],
        default=1
    )
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    USERNAME_FIELD = 'email'
    REQUIRED_FIELDS = ['username']

    class Meta:
        db_table = 'core_users'
        ordering = ['-created_at']

    def __str__(self):
        return f"{self.email} ({self.get_permissions_level_display()})"


class Branch(models.Model):
    """Company branches with Google Maps location."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    address = models.TextField()
    latitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    longitude = models.DecimalField(max_digits=10, decimal_places=7, null=True, blank=True)
    phone = models.CharField(max_length=30, blank=True)
    manager = models.ForeignKey(
        User, on_delete=models.SET_NULL, null=True, blank=True,
        related_name='managed_branches'
    )
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core_branches'
        ordering = ['name']

    def __str__(self):
        return self.name


class Warehouse(models.Model):
    """Branch warehouses / sub-warehouses."""
    id = models.UUIDField(primary_key=True, default=uuid.uuid4, editable=False)
    name = models.CharField(max_length=200)
    code = models.CharField(max_length=20, unique=True)
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='warehouses')
    parent_warehouse = models.ForeignKey(
        'self', on_delete=models.CASCADE, null=True, blank=True,
        related_name='sub_warehouses'
    )
    capacity = models.PositiveIntegerField(default=0, help_text='Max items')
    current_occupancy = models.PositiveIntegerField(default=0)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    class Meta:
        db_table = 'core_warehouses'
        ordering = ['branch__name', 'name']

    def __str__(self):
        return f"{self.name} ({self.branch.name})"

    @property
    def occupancy_rate(self):
        if self.capacity == 0:
            return 0
        return round((self.current_occupancy / self.capacity) * 100, 2)
