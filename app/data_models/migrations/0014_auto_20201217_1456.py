# Generated by Django 2.2.3 on 2020-12-17 20:56

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("data_models", "0013_auto_20201210_2326"),
    ]

    operations = [
        migrations.RemoveField(
            model_name="campaign",
            name="nasa_missions",
        ),
        migrations.AddField(
            model_name="campaign",
            name="nasa_missions",
            field=models.TextField(blank=True, default=""),
        ),
        migrations.DeleteModel(
            name="NasaMission",
        ),
    ]
