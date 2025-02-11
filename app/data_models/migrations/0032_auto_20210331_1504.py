# Generated by Django 3.1.3 on 2021-03-31 20:04

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("data_models", "0031_auto_20210331_1413"),
    ]

    operations = [
        migrations.RenameField(
            model_name="focusarea",
            old_name="priority",
            new_name="order_priority",
        ),
        migrations.RenameField(
            model_name="geographicalregion",
            old_name="priority",
            new_name="order_priority",
        ),
        migrations.RenameField(
            model_name="geophysicalconcept",
            old_name="priority",
            new_name="order_priority",
        ),
        migrations.RenameField(
            model_name="homebase",
            old_name="priority",
            new_name="order_priority",
        ),
        migrations.RenameField(
            model_name="measurementregion",
            old_name="priority",
            new_name="order_priority",
        ),
        migrations.RenameField(
            model_name="measurementstyle",
            old_name="priority",
            new_name="order_priority",
        ),
        migrations.RenameField(
            model_name="measurementtype",
            old_name="priority",
            new_name="order_priority",
        ),
        migrations.RenameField(
            model_name="partnerorg",
            old_name="priority",
            new_name="order_priority",
        ),
        migrations.RenameField(
            model_name="platformtype",
            old_name="priority",
            new_name="order_priority",
        ),
        migrations.RenameField(
            model_name="repository",
            old_name="priority",
            new_name="order_priority",
        ),
        migrations.RenameField(
            model_name="season",
            old_name="priority",
            new_name="order_priority",
        ),
        migrations.RenameField(
            model_name="websitetype",
            old_name="priority",
            new_name="order_priority",
        ),
    ]
