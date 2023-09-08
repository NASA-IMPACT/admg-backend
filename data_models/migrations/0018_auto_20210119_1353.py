# Generated by Django 3.1.3 on 2021-01-19 19:53

from django.db import migrations, models


class Migration(migrations.Migration):
    dependencies = [
        ("data_models", "0017_auto_20210104_1156"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="doi",
            options={"verbose_name": "DOI"},
        ),
        migrations.AlterField(
            model_name="instrument",
            name="arbitrary_characteristics",
            field=models.JSONField(blank=True, default=None, null=True),
        ),
    ]