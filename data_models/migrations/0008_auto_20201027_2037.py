# Generated by Django 2.2.3 on 2020-10-28 01:37

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("data_models", "0007_auto_20201025_1740"),
    ]

    operations = [
        migrations.AlterField(
            model_name="gcmdplatform",
            name="description",
            field=models.TextField(blank=True, default=""),
        ),
    ]
