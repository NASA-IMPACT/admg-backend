# Generated by Django 2.0.8 on 2020-03-05 16:50

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='AircraftType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('short_name', models.CharField(max_length=256, unique=True)),
                ('long_name', models.CharField(max_length=256)),
                ('description', models.CharField(max_length=256)),
                ('gcmd_translation', models.CharField(max_length=256)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Campaign',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('short_name', models.CharField(max_length=80, unique=True)),
                ('long_name', models.CharField(max_length=512)),
                ('description_edited', models.CharField(max_length=2048)),
                ('description', models.CharField(max_length=2048)),
                ('scientific_objective_focus_phenomena', models.CharField(max_length=512)),
                ('region', models.CharField(max_length=512)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('significant_events', models.CharField(max_length=512)),
                ('funding_program', models.CharField(max_length=256)),
                ('responsible_funding_program_lead', models.CharField(max_length=256)),
                ('responsible_or_project_lead', models.CharField(max_length=256)),
                ('technical_contact', models.CharField(max_length=256)),
                ('non_aircraft_platforms', models.CharField(max_length=512)),
                ('non_airborne_instruments', models.CharField(max_length=512)),
                ('total_flights', models.PositiveIntegerField()),
                ('doi', models.CharField(max_length=1024)),
                ('publication', models.CharField(max_length=1024)),
                ('supported_nasa_mission', models.CharField(max_length=512)),
                ('number_of_published_data_products', models.PositiveIntegerField()),
                ('data_total_volume', models.CharField(max_length=256)),
                ('project_data_repository_website', models.CharField(max_length=512)),
                ('other_resources', models.CharField(max_length=2048)),
                ('is_ongoing', models.BooleanField()),
                ('notes_public', models.CharField(max_length=2048)),
                ('notes_internal', models.CharField(max_length=2048)),
            ],
        ),
        migrations.CreateModel(
            name='Deployment',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('deployment_id', models.CharField(max_length=80)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('number_of_flights', models.PositiveIntegerField()),
                ('deployment_long_name', models.CharField(max_length=512)),
                ('notes_public', models.CharField(max_length=2048)),
                ('campaign', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='deployments', to='data_models.Campaign')),
            ],
        ),
        migrations.CreateModel(
            name='Flight',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('asp_longname', models.CharField(max_length=512)),
                ('info_from_asp', models.CharField(max_length=80)),
                ('home_base', models.CharField(max_length=256)),
                ('campaign_deployment_base', models.CharField(max_length=256)),
                ('owner', models.CharField(max_length=256)),
                ('technical_contact', models.CharField(max_length=256)),
                ('deployment_instrument_information_source', models.CharField(max_length=1024)),
                ('notes_public', models.CharField(max_length=2048)),
                ('deployment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='flights', to='data_models.Deployment')),
            ],
        ),
        migrations.CreateModel(
            name='FocusArea',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('short_name', models.CharField(max_length=256, unique=True)),
                ('long_name', models.CharField(max_length=256)),
                ('description', models.CharField(max_length=256)),
                ('gcmd_translation', models.CharField(max_length=256)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='GcmdInstrument',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('short_name', models.CharField(max_length=256, unique=True)),
                ('long_name', models.CharField(max_length=256)),
                ('uuid', models.UUIDField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='GcmdPhenomena',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('short_name', models.CharField(max_length=256, unique=True)),
                ('long_name', models.CharField(max_length=256)),
                ('uuid', models.UUIDField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='GcmdPlatform',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('short_name', models.CharField(max_length=256, unique=True)),
                ('long_name', models.CharField(max_length=256)),
                ('uuid', models.UUIDField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='GcmdProject',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('short_name', models.CharField(max_length=256, unique=True)),
                ('long_name', models.CharField(max_length=256)),
                ('uuid', models.UUIDField()),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='GeographicalRegion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('short_name', models.CharField(max_length=256, unique=True)),
                ('long_name', models.CharField(max_length=256)),
                ('description', models.CharField(max_length=256)),
                ('gcmd_translation', models.CharField(max_length=256)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='HomeBase',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('short_name', models.CharField(max_length=256, unique=True)),
                ('long_name', models.CharField(max_length=256)),
                ('description', models.CharField(max_length=256)),
                ('gcmd_translation', models.CharField(max_length=256)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Instrument',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('short_name', models.CharField(max_length=80, unique=True)),
                ('long_name', models.CharField(max_length=256)),
                ('instrument_description', models.CharField(max_length=256)),
                ('instrument_pi', models.CharField(max_length=256)),
                ('instrument_technical_contact', models.CharField(max_length=256)),
                ('facility_instrument_location', models.CharField(max_length=256)),
                ('funding_source', models.CharField(max_length=256)),
                ('spatial_resolution', models.CharField(max_length=256)),
                ('temporal_resolution', models.CharField(max_length=256)),
                ('radiometric_frequency', models.CharField(max_length=256)),
                ('calibration_information', models.CharField(max_length=1024)),
                ('initial_deployment_date', models.DateField()),
                ('dates_of_operation', models.CharField(max_length=512)),
                ('typical_number_of_data_products_per_level', models.CharField(max_length=256)),
                ('instrument_manufacturer', models.CharField(max_length=512)),
                ('resource_urls', models.CharField(max_length=2048)),
                ('instrument_doi', models.CharField(max_length=1024)),
                ('notes_public', models.CharField(max_length=2048)),
                ('gcmd_instruments', models.ManyToManyField(related_name='instruments', to='data_models.GcmdInstrument')),
            ],
        ),
        migrations.CreateModel(
            name='InstrumentType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('short_name', models.CharField(max_length=256, unique=True)),
                ('long_name', models.CharField(max_length=256)),
                ('description', models.CharField(max_length=256)),
                ('gcmd_translation', models.CharField(max_length=256)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='IopSe',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_iop', models.BooleanField()),
                ('short_name', models.CharField(max_length=80)),
                ('start_date', models.DateField()),
                ('end_date', models.DateField()),
                ('iop_description', models.CharField(max_length=1024)),
                ('regional_description', models.CharField(max_length=512)),
                ('published_list', models.CharField(max_length=1024)),
                ('reports', models.CharField(max_length=1024)),
                ('reference_file', models.CharField(max_length=1024)),
                ('deployment', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='iops', to='data_models.Deployment')),
            ],
        ),
        migrations.CreateModel(
            name='MeasurementKeyword',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('short_name', models.CharField(max_length=256, unique=True)),
                ('long_name', models.CharField(max_length=256)),
                ('description', models.CharField(max_length=256)),
                ('gcmd_translation', models.CharField(max_length=256)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='MeasurementRegion',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('short_name', models.CharField(max_length=256, unique=True)),
                ('long_name', models.CharField(max_length=256)),
                ('description', models.CharField(max_length=256)),
                ('gcmd_translation', models.CharField(max_length=256)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='PartnerOrg',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('short_name', models.CharField(max_length=256, unique=True)),
                ('long_name', models.CharField(max_length=256)),
                ('website', models.CharField(max_length=256)),
                ('notes_public', models.CharField(max_length=2048)),
            ],
        ),
        migrations.CreateModel(
            name='Platform',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('short_name', models.CharField(max_length=80, unique=True)),
                ('long_name', models.CharField(max_length=256)),
                ('platform_model', models.CharField(max_length=256)),
                ('desciption', models.CharField(max_length=256)),
                ('resource_urls', models.CharField(max_length=512)),
                ('notes_public', models.CharField(max_length=2048)),
                ('gcmd_platform', models.ManyToManyField(related_name='platforms', to='data_models.GcmdProject')),
                ('home_base', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='platforms', to='data_models.HomeBase')),
                ('platform_type', models.ForeignKey(null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='platforms', to='data_models.AircraftType')),
            ],
        ),
        migrations.CreateModel(
            name='PlatformType',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('short_name', models.CharField(max_length=256, unique=True)),
                ('long_name', models.CharField(max_length=256)),
                ('description', models.CharField(max_length=256)),
                ('gcmd_translation', models.CharField(max_length=256)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Repository',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('short_name', models.CharField(max_length=256, unique=True)),
                ('long_name', models.CharField(max_length=256)),
                ('description', models.CharField(max_length=256)),
                ('gcmd_translation', models.CharField(max_length=256)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.CreateModel(
            name='Season',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('short_name', models.CharField(max_length=256, unique=True)),
                ('long_name', models.CharField(max_length=256)),
                ('description', models.CharField(max_length=256)),
                ('gcmd_translation', models.CharField(max_length=256)),
            ],
            options={
                'abstract': False,
            },
        ),
        migrations.AddField(
            model_name='instrument',
            name='instrument_type',
            field=models.ManyToManyField(related_name='instruments', to='data_models.InstrumentType'),
        ),
        migrations.AddField(
            model_name='instrument',
            name='measurement_keywords',
            field=models.ManyToManyField(related_name='instruments', to='data_models.MeasurementKeyword'),
        ),
        migrations.AddField(
            model_name='instrument',
            name='measurement_regions',
            field=models.ManyToManyField(related_name='instruments', to='data_models.MeasurementRegion'),
        ),
        migrations.AddField(
            model_name='instrument',
            name='repositories',
            field=models.ManyToManyField(related_name='instruments', to='data_models.Repository'),
        ),
        migrations.AddField(
            model_name='flight',
            name='instruments',
            field=models.ManyToManyField(related_name='flights', to='data_models.Instrument'),
        ),
        migrations.AddField(
            model_name='flight',
            name='platform',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='flights', to='data_models.Platform'),
        ),
        migrations.AddField(
            model_name='deployment',
            name='geographical_regions',
            field=models.ManyToManyField(related_name='deployments', to='data_models.GeographicalRegion'),
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
            field=models.ManyToManyField(related_name='campaigns', to='data_models.GcmdProject'),
        ),
        migrations.AddField(
            model_name='campaign',
            name='partner_orgs',
            field=models.ManyToManyField(related_name='campaigns', to='data_models.PartnerOrg'),
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
    ]
