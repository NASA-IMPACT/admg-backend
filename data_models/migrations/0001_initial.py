# Generated by Django 2.2.3 on 2020-05-06 16:53

import django.contrib.gis.db.models.fields
import django.contrib.postgres.fields.jsonb
from django.db import migrations, models
import django.db.models.deletion
import uuid


class Migration(migrations.Migration):

    initial = True

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
    ]

    operations = [
        migrations.CreateModel(
            name='Campaign',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('short_name', models.CharField(max_length=256)),
                ('long_name', models.CharField(max_length=512, unique=True)),
                ('notes_internal', models.CharField(blank=True, default='', max_length=2048)),
                ('notes_public', models.CharField(blank=True, default='', max_length=2048)),
                ('description_short', models.CharField(blank=True, default='', max_length=2048)),
                ('description_long', models.CharField(blank=True, default='', max_length=2048)),
                ('focus_phenomena', models.CharField(max_length=1024)),
                ('region_description', models.CharField(max_length=1024)),
                ('spatial_bounds', django.contrib.gis.db.models.fields.PolygonField(blank=True, null=True, srid=4326)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField(blank=True, null=True)),
                ('funding_agency', models.CharField(max_length=256)),
                ('funding_program', models.CharField(blank=True, default='', max_length=256)),
                ('funding_program_lead', models.CharField(blank=True, default='', max_length=256)),
                ('lead_investigator', models.CharField(max_length=256)),
                ('technical_contact', models.CharField(blank=True, default='', max_length=256)),
                ('nonaircraft_platforms', models.CharField(blank=True, default='', max_length=1024)),
                ('nonaircraft_instruments', models.CharField(blank=True, default='', max_length=1024)),
                ('number_flights', models.PositiveIntegerField()),
                ('doi', models.CharField(blank=True, default='', max_length=1024)),
                ('number_data_products', models.PositiveIntegerField(blank=True, null=True)),
                ('data_volume', models.CharField(blank=True, max_length=256, null=True)),
                ('cmr_metadata', django.contrib.postgres.fields.jsonb.JSONField(blank=True, null=True)),
                ('repository_website', models.CharField(blank=True, default='', max_length=512)),
                ('project_website', models.CharField(blank=True, default='', max_length=512)),
                ('tertiary_website', models.CharField(blank=True, default='', max_length=512)),
                ('publication_links', models.CharField(blank=True, default='', max_length=2048)),
                ('other_resources', models.CharField(blank=True, default='', max_length=2048)),
                ('ongoing', models.BooleanField()),
                ('nasa_led', models.BooleanField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Deployment',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('short_name', models.CharField(max_length=256)),
                ('long_name', models.CharField(max_length=512, unique=True)),
                ('notes_internal', models.CharField(blank=True, default='', max_length=2048)),
                ('notes_public', models.CharField(blank=True, default='', max_length=2048)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('number_flights', models.PositiveIntegerField(blank=True, null=True)),
                ('campaign', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='deployments', to='data_models.Campaign')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='FocusArea',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('short_name', models.CharField(max_length=256, unique=True)),
                ('long_name', models.CharField(blank=True, default='', max_length=512)),
                ('notes_public', models.CharField(blank=True, default='', max_length=2048)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='GcmdInstrument',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('short_name', models.CharField(max_length=256, unique=True)),
                ('long_name', models.CharField(blank=True, default='', max_length=512)),
                ('instrument_category', models.CharField(blank=True, default='', max_length=256)),
                ('instrument_class', models.CharField(blank=True, default='', max_length=256)),
                ('instrument_type', models.CharField(blank=True, default='', max_length=256)),
                ('instrument_subtype', models.CharField(blank=True, default='', max_length=256)),
                ('gcmd_uuid', models.UUIDField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='GcmdPhenomena',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('category', models.CharField(max_length=256)),
                ('topic', models.CharField(blank=True, default='', max_length=256)),
                ('term', models.CharField(blank=True, default='', max_length=256)),
                ('variable_1', models.CharField(blank=True, default='', max_length=256)),
                ('variable_2', models.CharField(blank=True, default='', max_length=256)),
                ('variable_3', models.CharField(blank=True, default='', max_length=256)),
                ('gcmd_uuid', models.UUIDField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='GcmdPlatform',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('short_name', models.CharField(max_length=256, unique=True)),
                ('long_name', models.CharField(blank=True, default='', max_length=512)),
                ('category', models.CharField(max_length=256)),
                ('series_entry', models.CharField(max_length=256)),
                ('description', models.CharField(max_length=256)),
                ('gcmd_uuid', models.UUIDField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='GcmdProject',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('short_name', models.CharField(max_length=256, unique=True)),
                ('long_name', models.CharField(blank=True, default='', max_length=512)),
                ('bucket', models.CharField(max_length=256)),
                ('gcmd_uuid', models.UUIDField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='GeographicalRegion',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('short_name', models.CharField(max_length=256, unique=True)),
                ('long_name', models.CharField(blank=True, default='', max_length=512)),
                ('notes_public', models.CharField(blank=True, default='', max_length=2048)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='GeophysicalConcepts',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('short_name', models.CharField(max_length=256, unique=True)),
                ('long_name', models.CharField(blank=True, default='', max_length=512)),
                ('notes_public', models.CharField(blank=True, default='', max_length=2048)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='HomeBase',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('short_name', models.CharField(max_length=256, unique=True)),
                ('long_name', models.CharField(blank=True, default='', max_length=512)),
                ('notes_public', models.CharField(blank=True, default='', max_length=2048)),
                ('gcmd_translation', models.UUIDField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='InstrumentType',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('short_name', models.CharField(max_length=256, unique=True)),
                ('long_name', models.CharField(blank=True, default='', max_length=512)),
                ('notes_public', models.CharField(blank=True, default='', max_length=2048)),
                ('gcmd_translation', models.UUIDField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='IOP',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('short_name', models.CharField(max_length=256)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('description', models.CharField(max_length=1024)),
                ('region_description', models.CharField(max_length=512)),
                ('published_list', models.CharField(blank=True, default='', max_length=1024)),
                ('reports', models.CharField(blank=True, default='', max_length=1024)),
                ('reference_file', models.CharField(blank=True, default='', max_length=1024)),
                ('deployment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='iops', to='data_models.Deployment')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='MeasurementRegion',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('short_name', models.CharField(max_length=256, unique=True)),
                ('long_name', models.CharField(blank=True, default='', max_length=512)),
                ('notes_public', models.CharField(blank=True, default='', max_length=2048)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='NasaMission',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('short_name', models.CharField(max_length=256, unique=True)),
                ('long_name', models.CharField(blank=True, default='', max_length=512)),
                ('notes_public', models.CharField(blank=True, default='', max_length=2048)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PartnerOrg',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('short_name', models.CharField(max_length=256, unique=True)),
                ('long_name', models.CharField(blank=True, default='', max_length=512)),
                ('notes_public', models.CharField(blank=True, default='', max_length=2048)),
                ('website', models.CharField(max_length=256)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Repository',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('short_name', models.CharField(max_length=256, unique=True)),
                ('long_name', models.CharField(blank=True, default='', max_length=512)),
                ('notes_public', models.CharField(blank=True, default='', max_length=2048)),
                ('gcmd_translation', models.UUIDField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Season',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('short_name', models.CharField(max_length=256, unique=True)),
                ('long_name', models.CharField(blank=True, default='', max_length=512)),
                ('notes_public', models.CharField(blank=True, default='', max_length=2048)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='SignificantEvent',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('short_name', models.CharField(max_length=256)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('description', models.CharField(max_length=1024)),
                ('region_description', models.CharField(max_length=512)),
                ('published_list', models.CharField(blank=True, default='', max_length=1024)),
                ('reports', models.CharField(blank=True, default='', max_length=1024)),
                ('reference_file', models.CharField(blank=True, default='', max_length=1024)),
                ('deployment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='significant_events', to='data_models.Deployment')),
                ('iop', models.ForeignKey(null=True, on_delete=django.db.models.deletion.CASCADE, related_name='significant_events', to='data_models.IOP')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PlatformType',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('short_name', models.CharField(max_length=256, unique=True)),
                ('long_name', models.CharField(blank=True, default='', max_length=512)),
                ('notes_public', models.CharField(blank=True, default='', max_length=2048)),
                ('gcmd_translation', models.UUIDField(blank=True, null=True)),
                ('example', models.CharField(blank=True, default='', max_length=256)),
                ('parent', models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='sub_types', to='data_models.PlatformType')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Platform',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('short_name', models.CharField(max_length=256)),
                ('long_name', models.CharField(max_length=512, unique=True)),
                ('notes_internal', models.CharField(blank=True, default='', max_length=2048)),
                ('notes_public', models.CharField(blank=True, default='', max_length=2048)),
                ('desciption', models.CharField(max_length=256)),
                ('online_information', models.CharField(blank=True, default='', max_length=512)),
                ('staionary', models.BooleanField()),
                ('gcmd_platform', models.ManyToManyField(blank=True, default='', related_name='platforms', to='data_models.GcmdPlatform')),
                ('platform_type', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='platforms', to='data_models.PlatformType')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Instrument',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('short_name', models.CharField(max_length=256)),
                ('long_name', models.CharField(max_length=512, unique=True)),
                ('notes_internal', models.CharField(blank=True, default='', max_length=2048)),
                ('notes_public', models.CharField(blank=True, default='', max_length=2048)),
                ('description', models.CharField(max_length=256)),
                ('lead_investigator', models.CharField(blank=True, default='', max_length=256)),
                ('technical_contact', models.CharField(max_length=256)),
                ('facility', models.CharField(blank=True, default='', max_length=256)),
                ('funding_source', models.CharField(blank=True, default='', max_length=256)),
                ('spatial_resolution', models.CharField(max_length=256)),
                ('temporal_resolution', models.CharField(max_length=256)),
                ('radiometric_frequency', models.CharField(max_length=256)),
                ('calibration_information', models.CharField(blank=True, default='', max_length=1024)),
                ('data_products_per_level', models.CharField(blank=True, default='', max_length=256)),
                ('instrument_manufacturer', models.CharField(blank=True, default='', max_length=512)),
                ('online_information', models.CharField(blank=True, default='', max_length=2048)),
                ('instrument_doi', models.CharField(blank=True, default='', max_length=1024)),
                ('gcmd_instruments', models.ManyToManyField(blank=True, default='', related_name='instruments', to='data_models.GcmdInstrument')),
                ('gcmd_phenomenas', models.ManyToManyField(related_name='instruments', to='data_models.GcmdPhenomena')),
                ('geophysical_concepts', models.ManyToManyField(related_name='instruments', to='data_models.GeophysicalConcepts')),
                ('instrument_types', models.ManyToManyField(related_name='instruments', to='data_models.InstrumentType')),
                ('measurement_regions', models.ManyToManyField(related_name='instruments', to='data_models.MeasurementRegion')),
                ('repositories', models.ManyToManyField(blank=True, default='', related_name='instruments', to='data_models.Repository')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='deployment',
            name='geographical_regions',
            field=models.ManyToManyField(blank=True, default='', related_name='deployments', to='data_models.GeographicalRegion'),
        ),
        migrations.CreateModel(
            name='CollectionPeriod',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('asp_long_name', models.CharField(blank=True, default='', max_length=512)),
                ('platform_identifier', models.CharField(blank=True, default='', max_length=128)),
                ('home_base', models.CharField(blank=True, default='', max_length=256)),
                ('campaign_deployment_base', models.CharField(blank=True, default='', max_length=256)),
                ('platform_owner', models.CharField(blank=True, default='', max_length=256)),
                ('platform_technical_contact', models.CharField(blank=True, default='', max_length=256)),
                ('instrument_information_source', models.CharField(blank=True, default='', max_length=1024)),
                ('notes_internal', models.CharField(blank=True, default='', max_length=2048)),
                ('notes_public', models.CharField(blank=True, default='', max_length=2048)),
                ('num_ventures', models.PositiveIntegerField(blank=True, null=True)),
                ('auto_generated', models.BooleanField()),
                ('deployment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='flights', to='data_models.Deployment')),
                ('instruments', models.ManyToManyField(related_name='flights', to='data_models.Instrument')),
                ('platform', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='flights', to='data_models.Platform')),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='campaign',
            name='focus_areas',
            field=models.ManyToManyField(related_name='campaigns', to='data_models.FocusArea'),
        ),
        migrations.AddField(
            model_name='campaign',
            name='gcmd_phenomenas',
            field=models.ManyToManyField(related_name='campaigns', to='data_models.GcmdPhenomena'),
        ),
        migrations.AddField(
            model_name='campaign',
            name='gcmd_project',
            field=models.ManyToManyField(blank=True, default='', related_name='campaigns', to='data_models.GcmdProject'),
        ),
        migrations.AddField(
            model_name='campaign',
            name='geophysical_concepts',
            field=models.ManyToManyField(related_name='campaigns', to='data_models.GeophysicalConcepts'),
        ),
        migrations.AddField(
            model_name='campaign',
            name='nasa_mission',
            field=models.ManyToManyField(blank=True, default='', related_name='campaigns', to='data_models.NasaMission'),
        ),
        migrations.AddField(
            model_name='campaign',
            name='partner_orgs',
            field=models.ManyToManyField(blank=True, default='', related_name='campaigns', to='data_models.PartnerOrg'),
        ),
        migrations.AddField(
            model_name='campaign',
            name='platform_types',
            field=models.ManyToManyField(related_name='campaigns', to='data_models.PlatformType'),
        ),
        migrations.AddField(
            model_name='campaign',
            name='repositories',
            field=models.ManyToManyField(related_name='campaigns', to='data_models.Repository'),
        ),
        migrations.AddField(
            model_name='campaign',
            name='seasons',
            field=models.ManyToManyField(related_name='campaigns', to='data_models.Season'),
        ),
        migrations.CreateModel(
            name='Alias',
            fields=[
                ('uuid', models.UUIDField(default=uuid.uuid4, editable=False, primary_key=True, serialize=False, unique=True)),
                ('object_id', models.UUIDField()),
                ('short_name', models.CharField(max_length=256, unique=True)),
                ('long_name', models.CharField(blank=True, default='', max_length=512)),
                ('source', models.CharField(blank=True, default='', max_length=2048)),
                ('content_type', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='contenttypes.ContentType')),
            ],
            options={
                'verbose_name_plural': 'Aliases',
            },
        ),
    ]
