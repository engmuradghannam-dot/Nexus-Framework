from django.core.validators import MaxValueValidator, MinLengthValidator, MinValueValidator
from django.db import models
from django.contrib.auth.models import User

from .validators import alphanumeric_validator

LATITUDE_VALIDATORS = [MinValueValidator(-90), MaxValueValidator(90)]
LONGITUDE_VALIDATORS = [MinValueValidator(-180), MaxValueValidator(180)]


class Company(models.Model):
    name = models.CharField(max_length=255, validators=[MinLengthValidator(2)])
    description = models.TextField(blank=True)
    address = models.TextField(blank=True)
    latitude = models.FloatField(null=True, blank=True, validators=LATITUDE_VALIDATORS)
    longitude = models.FloatField(null=True, blank=True, validators=LONGITUDE_VALIDATORS)
    created_at = models.DateTimeField(auto_now_add=True)
    updated_at = models.DateTimeField(auto_now=True)

    class Meta:
        verbose_name_plural = "Companies"

    def __str__(self):
        return self.name

class Branch(models.Model):
    company = models.ForeignKey(Company, on_delete=models.CASCADE, related_name='branches')
    name = models.CharField(max_length=255, validators=[MinLengthValidator(2)])
    address = models.TextField(blank=True)
    latitude = models.FloatField(null=True, blank=True, validators=LATITUDE_VALIDATORS)
    longitude = models.FloatField(null=True, blank=True, validators=LONGITUDE_VALIDATORS)
    is_active = models.BooleanField(default=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.company.name} - {self.name}"

class Warehouse(models.Model):
    branch = models.ForeignKey(Branch, on_delete=models.CASCADE, related_name='warehouses')
    name = models.CharField(max_length=255, validators=[MinLengthValidator(2)])
    code = models.CharField(max_length=50, unique=True, validators=[alphanumeric_validator])
    is_main = models.BooleanField(default=False)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.branch.name} - {self.name}"

class SubWarehouse(models.Model):
    warehouse = models.ForeignKey(Warehouse, on_delete=models.CASCADE, related_name='sub_warehouses')
    name = models.CharField(max_length=255, validators=[MinLengthValidator(2)])
    code = models.CharField(max_length=50, unique=True, validators=[alphanumeric_validator])
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return f"{self.warehouse.name} - {self.name}"

class Department(models.Model):
    name = models.CharField(max_length=255, validators=[MinLengthValidator(2)])
    code = models.CharField(max_length=50, unique=True, validators=[alphanumeric_validator])
    description = models.TextField(blank=True)
    created_at = models.DateTimeField(auto_now_add=True)

    def __str__(self):
        return self.name

class HRProfile(models.Model):
    user = models.OneToOneField(User, on_delete=models.CASCADE, related_name='hr_profile')
    employee_id = models.CharField(max_length=50, unique=True)
    department = models.ForeignKey(Department, on_delete=models.SET_NULL, null=True, blank=True)
    branch = models.ForeignKey(Branch, on_delete=models.SET_NULL, null=True, blank=True)
    role = models.CharField(max_length=100)
    permissions = models.JSONField(default=dict, blank=True)
    is_active = models.BooleanField(default=True)
    joined_date = models.DateField(null=True, blank=True)

    def __str__(self):
        return f"{self.user.username} - {self.employee_id}"
