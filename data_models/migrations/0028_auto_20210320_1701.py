# Generated by Django 3.1.3 on 2021-03-20 22:01

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("data_models", "0027_auto_20210304_1329"),
    ]

    operations = [
        migrations.AlterField(
            model_name="doi",
            name="doi",
            field=models.CharField(blank=True, default="", max_length=512, null=True),
        ),
    ]
