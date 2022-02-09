# Generated by Django 3.1.3 on 2021-02-24 04:32

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ("api_app", "0009_auto_20210223_2039"),
    ]

    operations = [
        migrations.CreateModel(
            name="ApprovalLog",
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
                            (2, "edit"),
                            (3, "submit"),
                            (4, "review"),
                            (5, "publish"),
                            (6, "reject"),
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
                        related_name="user",
                        to=settings.AUTH_USER_MODEL,
                    ),
                ),
            ],
        ),
        migrations.DeleteModel(
            name="ChangeLog",
        ),
    ]
