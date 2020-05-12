# Generated by Django 2.2.3 on 2020-05-07 20:47

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_models', '0003_auto_20200507_1536'),
    ]

    operations = [
        migrations.AddField(
            model_name='geographicalregion',
            name='example',
            field=models.CharField(blank=True, default='', max_length=256),
        ),
        migrations.AddField(
            model_name='geographicalregion',
            name='gcmd_uuid',
            field=models.UUIDField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='geophysicalconcept',
            name='example',
            field=models.CharField(blank=True, default='', max_length=256),
        ),
        migrations.AddField(
            model_name='geophysicalconcept',
            name='gcmd_uuid',
            field=models.UUIDField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='measurementregion',
            name='example',
            field=models.CharField(blank=True, default='', max_length=256),
        ),
    ]
