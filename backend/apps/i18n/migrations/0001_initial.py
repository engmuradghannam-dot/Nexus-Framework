# Generated manually for Nexus Framework

import django.db.models.deletion
from django.db import migrations, models

import uuid


class Migration(migrations.Migration):
    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="Language",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("code", models.CharField(db_index=True, help_text="ISO 639-1 code + optional region", max_length=10, unique=True)),
                ("name", models.CharField(max_length=100)),
                ("name_local", models.CharField(help_text="Native name", max_length=100)),
                ("direction", models.CharField(choices=[("ltr", "Left-to-Right"), ("rtl", "Right-to-Left")], default="ltr", max_length=3)),
                ("is_active", models.BooleanField(default=True)),
                ("is_default", models.BooleanField(default=False)),
                ("flag_emoji", models.CharField(blank=True, max_length=10)),
                ("decimal_separator", models.CharField(default=".", max_length=5)),
                ("thousands_separator", models.CharField(default=",", max_length=5)),
                ("date_format", models.CharField(default="YYYY-MM-DD", max_length=50)),
                ("time_format", models.CharField(default="HH:mm", max_length=50)),
                ("first_day_of_week", models.PositiveSmallIntegerField(default=1, help_text="1=Monday, 7=Sunday")),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
            ],
            options={
                "ordering": ["name"],
                "verbose_name": "Language",
                "verbose_name_plural": "Languages",
            },
        ),
        migrations.CreateModel(
            name="Translation",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("key", models.CharField(db_index=True, max_length=500)),
                ("value", models.TextField()),
                ("context", models.CharField(blank=True, db_index=True, help_text="Module or page context", max_length=200)),
                ("is_reviewed", models.BooleanField(default=False)),
                ("reviewed_by", models.CharField(blank=True, max_length=100)),
                ("reviewed_at", models.DateTimeField(blank=True, null=True)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("updated_at", models.DateTimeField(auto_now=True)),
                ("language", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="translations", to="i18n.language")),
            ],
            options={
                "ordering": ["key", "language"],
                "verbose_name": "Translation",
                "verbose_name_plural": "Translations",
            },
        ),
        migrations.AddConstraint(
            model_name="translation",
            constraint=models.UniqueConstraint(fields=("language", "key", "context"), name="unique_translation_lang_key_ctx"),
        ),
        migrations.AddIndex(
            model_name="translation",
            index=models.Index(fields=["key", "language"], name="i18n_transla_key_7f8b8c_idx"),
        ),
        migrations.AddIndex(
            model_name="translation",
            index=models.Index(fields=["context", "language"], name="i18n_transla_conte_3a2b1c_idx"),
        ),
        migrations.CreateModel(
            name="TranslationImportJob",
            fields=[
                ("id", models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False)),
                ("name", models.CharField(max_length=200)),
                ("file", models.FileField(upload_to="translation_imports/")),
                ("status", models.CharField(choices=[("pending", "Pending"), ("processing", "Processing"), ("completed", "Completed"), ("failed", "Failed")], default="pending", max_length=20)),
                ("total_rows", models.PositiveIntegerField(default=0)),
                ("processed_rows", models.PositiveIntegerField(default=0)),
                ("failed_rows", models.PositiveIntegerField(default=0)),
                ("error_log", models.JSONField(default=list)),
                ("created_by", models.CharField(max_length=100)),
                ("created_at", models.DateTimeField(auto_now_add=True)),
                ("completed_at", models.DateTimeField(blank=True, null=True)),
                ("language", models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name="import_jobs", to="i18n.language")),
            ],
            options={
                "ordering": ["-created_at"],
                "verbose_name": "Translation Import Job",
                "verbose_name_plural": "Translation Import Jobs",
            },
        ),
    ]
