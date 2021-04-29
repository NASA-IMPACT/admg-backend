# Generated by Django 3.1.3 on 2021-04-28 15:37

import django.contrib.gis.db.models.fields
from django.db import migrations, models
import django.db.models.deletion

def set_defaults(apps, schema_editor):
    WebsiteType = apps.get_model('data_models', 'WebsiteType')
    Website = apps.get_model('data_models', 'Website')
    default_type = WebsiteType.objects.first()

    for website in Website.objects.all().iterator():
        website.website_type = default_type
        website.save()


class Migration(migrations.Migration):

    dependencies = [
        ('data_models', '0035_auto_20210422_1613'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='deployment',
            name='number_collection_periods',
        ),
        migrations.RemoveField(
            model_name='website',
            name='website_types',
        ),
        migrations.AddField(
            model_name='deployment',
            name='spatial_bounds',
            field=django.contrib.gis.db.models.fields.PolygonField(blank=True, null=True, srid=4326),
        ),
        migrations.AlterField(
            model_name='campaign',
            name='funding_agency',
            field=models.CharField(blank=True, default='', max_length=256),
        ),
        migrations.AlterField(
            model_name='website',
            name='title',
            field=models.TextField(blank=True, default=''),
        ),
        migrations.AddField(
            model_name='website',
            name='website_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, null=True, blank=True, related_name='websites', to='data_models.websitetype'),
            preserve_default=False,
        ),
        migrations.RunPython(set_defaults),
        migrations.AlterField(
            model_name='website',
            name='website_type',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='websites', to='data_models.websitetype'),
            preserve_default=False,
        ),
    ]
