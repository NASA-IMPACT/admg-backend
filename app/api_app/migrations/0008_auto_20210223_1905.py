# Generated by Django 3.1.3 on 2021-02-24 01:05

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):
    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("api_app", "0007_auto_20210218_2128"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="change",
            name="added_date",
        ),
        migrations.RemoveField(
            model_name="change",
            name="notes",
        ),
        migrations.RemoveField(
            model_name="change",
            name="published_by",
        ),
        migrations.RemoveField(
            model_name="change",
            name="published_date",
        ),
        migrations.RemoveField(
            model_name="change",
            name="rejected_by",
        ),
        migrations.RemoveField(
            model_name="change",
            name="rejected_date",
        ),
        migrations.RemoveField(
            model_name="change",
            name="reviewed_by",
        ),
        migrations.RemoveField(
            model_name="change",
            name="reviewed_date",
        ),
        migrations.RemoveField(
            model_name="change",
            name="submitted_by",
        ),
        migrations.RemoveField(
            model_name="change",
            name="submitted_date",
        ),
        migrations.RemoveField(
            model_name="change",
            name="user",
        ),
        migrations.CreateModel(
            name="ChangeLog",
            fields=[
                (
                    "uuid",
                    models.UUIDField(
                        default=uuid.uuid4, editable=False, primary_key=True, serialize=False
                    ),
                ),
                ("date", models.DateTimeField(auto_now_add=True)),
                (
                    "action",
                    models.IntegerField(
                        choices=[
                            (1, "create"),
                            (2, "submit"),
                            (3, "review"),
                            (4, "publish"),
                            (5, "reject"),
                        ],
                        default=1,
                    ),
                ),
                ("notes", models.TextField(blank=True, default="")),
                (
                    "change",
                    models.ForeignKey(
                        blank=True, on_delete=django.db.models.deletion.CASCADE, to="api_app.change"
                    ),
                ),
                (
                    "user",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.SET_NULL,
                        related_name="submitted_by",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
    ]
