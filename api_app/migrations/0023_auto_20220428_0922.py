# Generated by Django 3.1.3 on 2022-04-28 14:22

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api_app', '0022_auto_20220428_0921'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='resolvedlist',
            name='change_uuid',
        ),
        migrations.DeleteModel(
            name='Recommendation',
        ),
        migrations.DeleteModel(
            name='ResolvedList',
        ),
    ]
