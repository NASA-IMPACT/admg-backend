# Generated by Django 2.2.3 on 2020-08-12 23:13

import data_models.models
from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("data_models", "0001_initial"),
    ]

    operations = [
        migrations.AlterField(
            model_name="image",
            name="image",
            field=models.ImageField(
                default="www.google.com", upload_to=data_models.models.get_file_path
            ),
            preserve_default=False,
        ),
    ]
