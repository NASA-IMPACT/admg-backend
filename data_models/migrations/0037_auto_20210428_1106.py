# Generated by Django 3.1.3 on 2021-04-28 16:06

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("data_models", "0036_auto_20210428_1037"),
    ]

    operations = [
        migrations.RenameField(
            model_name="collectionperiod",
            old_name="num_ventures",
            new_name="number_ventures",
        ),
        migrations.RemoveField(
            model_name="campaign",
            name="number_collection_periods",
        ),
    ]
