# Generated by Django 3.1.3 on 2021-02-09 16:50

import uuid

from django.db import migrations, models
import django.utils.timezone


class Migration(migrations.Migration):
    dependencies = [
        ("data_models", "0018_auto_20210119_1353"),
    ]

    operations = [
        migrations.RenameField(
            model_name="campaign",
            old_name="doi",
            new_name="campaign_doi",
        ),
        migrations.RenameField(
            model_name="doi",
            old_name="long_name",
            new_name="cmr_entry_title",
        ),
        migrations.RemoveField(
            model_name="collectionperiod",
            name="dois",
        ),
        migrations.RemoveField(
            model_name="doi",
            name="short_name",
        ),
        migrations.RemoveField(
            model_name="instrument",
            name="dois",
        ),
        migrations.RemoveField(
            model_name="platform",
            name="dois",
        ),
        migrations.AddField(
            model_name="doi",
            name="campaigns",
            field=models.ManyToManyField(related_name="dois", to="data_models.Campaign"),
        ),
        migrations.AddField(
            model_name="doi",
            name="cmr_dates",
            field=models.JSONField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name="doi",
            name="cmr_plats_and_insts",
            field=models.JSONField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name="doi",
            name="cmr_projects",
            field=models.JSONField(blank=True, default=None, null=True),
        ),
        migrations.AddField(
            model_name="doi",
            name="cmr_short_name",
            field=models.CharField(blank=True, default="", max_length=512),
        ),
        migrations.AddField(
            model_name="doi",
            name="collection_periods",
            field=models.ManyToManyField(related_name="dois", to="data_models.CollectionPeriod"),
        ),
        migrations.AddField(
            model_name="doi",
            name="concept_id",
            field=models.CharField(default=uuid.uuid4, max_length=512, unique=True),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="doi",
            name="date_queried",
            field=models.DateTimeField(default=django.utils.timezone.now),
            preserve_default=False,
        ),
        migrations.AddField(
            model_name="doi",
            name="doi",
            field=models.CharField(blank=True, default="", max_length=512),
        ),
        migrations.AddField(
            model_name="doi",
            name="instruments",
            field=models.ManyToManyField(related_name="dois", to="data_models.Instrument"),
        ),
        migrations.AddField(
            model_name="doi",
            name="platforms",
            field=models.ManyToManyField(related_name="dois", to="data_models.Platform"),
        ),
    ]
