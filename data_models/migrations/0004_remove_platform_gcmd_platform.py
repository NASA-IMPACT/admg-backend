# Generated by Django 2.0.8 on 2020-03-05 20:10

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data_models', '0003_auto_20200305_1408'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='platform',
            name='gcmd_platform',
        ),
    ]
