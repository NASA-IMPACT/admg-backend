# Generated by Django 4.1.5 on 2023-03-07 23:53

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ('data_models', '0051_auto_20220812_1746'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='campaign',
            name='spatial_bounds',
        ),
    ]
