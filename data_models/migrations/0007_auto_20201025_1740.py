# Generated by Django 2.2.3 on 2020-10-25 22:40

from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    dependencies = [
        ("data_models", "0006_auto_20201009_0715"),
    ]

    operations = [
        migrations.CreateModel(
            name="MeasurementStyle",
            fields=[
                (
                    "uuid",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                ("short_name", models.CharField(max_length=256, unique=True)),
                ("long_name", models.CharField(blank=True, default="", max_length=512)),
                ("notes_public", models.TextField(blank=True, default="")),
                ("example", models.CharField(blank=True, default="", max_length=1024)),
                (
                    "parent",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sub_types",
                        to="data_models.MeasurementStyle",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.CreateModel(
            name="MeasurementType",
            fields=[
                (
                    "uuid",
                    models.UUIDField(
                        default=uuid.uuid4,
                        editable=False,
                        primary_key=True,
                        serialize=False,
                        unique=True,
                    ),
                ),
                ("short_name", models.CharField(max_length=256, unique=True)),
                ("long_name", models.CharField(blank=True, default="", max_length=512)),
                ("notes_public", models.TextField(blank=True, default="")),
                ("example", models.CharField(blank=True, default="", max_length=1024)),
                (
                    "parent",
                    models.ForeignKey(
                        blank=True,
                        null=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        related_name="sub_types",
                        to="data_models.MeasurementType",
                    ),
                ),
            ],
            options={
                "abstract": False,
            },
        ),
        migrations.RemoveField(
            model_name="instrument",
            name="instrument_types",
        ),
        migrations.AlterField(
            model_name="geographicalregion",
            name="example",
            field=models.CharField(blank=True, default="", max_length=1024),
        ),
        migrations.AlterField(
            model_name="geophysicalconcept",
            name="example",
            field=models.CharField(blank=True, default="", max_length=1024),
        ),
        migrations.AlterField(
            model_name="measurementregion",
            name="example",
            field=models.CharField(blank=True, default="", max_length=1024),
        ),
        migrations.AlterField(
            model_name="platformtype",
            name="example",
            field=models.CharField(blank=True, default="", max_length=1024),
        ),
        migrations.DeleteModel(
            name="InstrumentType",
        ),
        migrations.AddField(
            model_name="instrument",
            name="measurement_style",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="data_models.MeasurementStyle",
            ),
        ),
        migrations.AddField(
            model_name="instrument",
            name="measurement_type",
            field=models.ForeignKey(
                blank=True,
                null=True,
                on_delete=django.db.models.deletion.SET_NULL,
                to="data_models.MeasurementType",
            ),
        ),
    ]
