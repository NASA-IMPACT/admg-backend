# Generated by Django 2.2.3 on 2020-12-11 05:26

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ("data_models", "0012_auto_20201202_1526"),
    ]

    operations = [
        migrations.AlterField(
            model_name="gcmdplatform",
            name="short_name",
            field=models.CharField(blank=True, default="", max_length=256),
        ),
    ]
