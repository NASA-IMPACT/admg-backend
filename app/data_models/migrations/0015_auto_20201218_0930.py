# Generated by Django 2.2.3 on 2020-12-18 15:30

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ("data_models", "0014_auto_20201217_1456"),
    ]

    operations = [
        migrations.AlterField(
            model_name="collectionperiod",
            name="home_base",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                related_name="collection_periods",
                to="data_models.HomeBase",
            ),
        ),
    ]