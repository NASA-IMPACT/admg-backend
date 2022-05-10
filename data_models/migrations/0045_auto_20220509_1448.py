# Generated by Django 3.1.3 on 2022-05-09 19:48

import django.contrib.postgres.fields
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_models', '0044_auto_20220203_1500'),
    ]

    operations = [
        migrations.AddField(
            model_name='doi',
            name='cmr_abstract',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='doi',
            name='cmr_data_formats',
            field=django.contrib.postgres.fields.ArrayField(base_field=models.CharField(blank=True, default='', max_length=512), blank=True, default=list, size=None),
        ),
        migrations.AddField(
            model_name='doi',
            name='cmr_science_keywords',
            field=models.JSONField(blank=True, default=None, null=True),
        ),
    ]
