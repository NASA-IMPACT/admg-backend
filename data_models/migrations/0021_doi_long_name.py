# Generated by Django 3.1.3 on 2021-02-12 16:18

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("data_models", "0020_auto_20210210_0033"),
    ]

    operations = [
        migrations.AddField(
            model_name="doi",
            name="long_name",
            field=models.TextField(blank=True, default=""),
        ),
    ]
