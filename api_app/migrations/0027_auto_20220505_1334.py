# Generated by Django 3.1.3 on 2022-05-05 18:34

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('api_app', '0026_auto_20220428_2121'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='resolvedlist',
            name='change',
        ),
        migrations.DeleteModel(
            name='Recommendation',
        ),
        migrations.DeleteModel(
            name='ResolvedList',
        ),
    ]
