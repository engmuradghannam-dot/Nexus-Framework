"""Models for the Controls Library.

Loaded from the master control workbooks:
  * Industry            <- Industry Catalog
  * IndustryControl     <- Industry Control Library
  * AIAgent             <- AI Agent Registry
  * MasterEntity        <- Entity Master Library
  * FormControl         <- All Controls Master
"""

from django.db import models


class Industry(models.Model):
    """A catalog entry describing a business industry / vertical."""

    code = models.CharField(max_length=30, unique=True)
    name = models.CharField(max_length=200)
    category = models.CharField(max_length=100, blank=True, db_index=True)
    description = models.TextField(blank=True)

    class Meta:
        db_table = "controls_industries"
        ordering = ["category", "name"]
        verbose_name_plural = "Industries"

    def __str__(self):
        return f"{self.code} - {self.name}"


class IndustryControl(models.Model):
    """A single control from the industry control library."""

    industry = models.CharField(max_length=200, db_index=True)
    module = models.CharField(max_length=200, blank=True)
    control_id = models.CharField(max_length=60, unique=True)
    control_name = models.CharField(max_length=200)
    sub_control = models.CharField(max_length=200, blank=True)
    description = models.TextField(blank=True)
    required = models.BooleanField(default=True)
    ai_agent = models.CharField(max_length=200, blank=True)
    database_entity = models.CharField(max_length=200, blank=True)
    kpi = models.CharField(max_length=200, blank=True)
    compliance = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = "controls_industry_controls"
        ordering = ["industry", "module", "control_id"]

    def __str__(self):
        return f"{self.control_id} - {self.control_name}"


class AIAgent(models.Model):
    """An AI agent responsible for a domain / entity."""

    industry = models.CharField(max_length=200, blank=True, db_index=True)
    name = models.CharField(max_length=200)
    responsibility = models.TextField(blank=True)
    database_entity = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = "controls_ai_agents"
        ordering = ["industry", "name"]

    def __str__(self):
        return self.name


class MasterEntity(models.Model):
    """A shared master-data entity used across industries."""

    name = models.CharField(max_length=200, unique=True)
    entity_type = models.CharField(max_length=100, blank=True)
    usage = models.CharField(max_length=200, blank=True)

    class Meta:
        db_table = "controls_master_entities"
        ordering = ["name"]
        verbose_name_plural = "Master entities"

    def __str__(self):
        return self.name


class FormControl(models.Model):
    """A single input/control on a form, with implementation status."""

    STATUS_PRESENT = "present"
    STATUS_MISSING = "missing"
    STATUS_PLANNED = "planned"
    STATUS_CHOICES = [
        (STATUS_PRESENT, "Present"),
        (STATUS_MISSING, "Missing"),
        (STATUS_PLANNED, "Planned"),
    ]
    PRIORITY_CHOICES = [
        ("High", "High"),
        ("Medium", "Medium"),
        ("Low", "Low"),
    ]

    seq = models.PositiveIntegerField(default=0)
    form_name = models.CharField(max_length=200, db_index=True)
    input_name = models.CharField(max_length=255)
    input_type = models.CharField(max_length=50, blank=True)
    status = models.CharField(
        max_length=20, choices=STATUS_CHOICES, default=STATUS_MISSING, db_index=True
    )
    priority = models.CharField(
        max_length=20, choices=PRIORITY_CHOICES, default="Medium", db_index=True
    )

    class Meta:
        db_table = "controls_form_controls"
        ordering = ["form_name", "seq"]
        unique_together = ["form_name", "input_name"]

    def __str__(self):
        return f"{self.form_name} / {self.input_name}"
