# Generated by Django 3.1.3 on 2021-04-30 03:31

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_models', '0038_website_notes_internal'),
    ]

    operations = [
        migrations.AlterField(
            model_name='website',
            name='url',
            field=models.URLField(max_length=1024, unique=True),
        ),
    ]
