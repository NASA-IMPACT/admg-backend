# Generated by Django 2.2.3 on 2020-12-18 15:53

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("data_models", "0015_auto_20201218_0930"),
    ]

    operations = [
        migrations.AddField(
            model_name="focusarea",
            name="notes_internal",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="geographicalregion",
            name="notes_internal",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="geophysicalconcept",
            name="notes_internal",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="homebase",
            name="notes_internal",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="measurementregion",
            name="notes_internal",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="measurementstyle",
            name="notes_internal",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="measurementtype",
            name="notes_internal",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="partnerorg",
            name="notes_internal",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="platformtype",
            name="notes_internal",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="repository",
            name="notes_internal",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.AddField(
            model_name="season",
            name="notes_internal",
            field=models.TextField(blank=True, default=""),
        ),
    ]
