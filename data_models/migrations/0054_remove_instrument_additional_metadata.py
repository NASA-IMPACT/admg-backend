# Generated by Django 4.1.5 on 2023-04-05 19:39

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('data_models', '0053_alter_doi_cmr_data_formats_alter_doi_cmr_dates_and_more'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='instrument',
            name='additional_metadata',
        ),
    ]
