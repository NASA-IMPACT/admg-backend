# Generated by Django 2.0.8 on 2020-03-05 20:11

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_models', '0004_remove_platform_gcmd_platform'),
    ]

    operations = [
        migrations.AddField(
            model_name='platform',
            name='gcmd_platform',
            field=models.ManyToManyField(related_name='platforms', to='data_models.GcmdPlatform'),
        ),
    ]
