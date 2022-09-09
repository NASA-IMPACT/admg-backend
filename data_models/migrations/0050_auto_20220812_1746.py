# Generated by Django 3.1.3 on 2022-08-12 22:46

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_models', '0049_update_doi_cmr_data_formats'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='gcmdinstrument',
            options={'ordering': ('short_name',), 'verbose_name': 'GCMD Instrument'},
        ),
        migrations.AlterModelOptions(
            name='gcmdplatform',
            options={'ordering': ('short_name',), 'verbose_name': 'GCMD Platform'},
        ),
        migrations.AlterModelOptions(
            name='gcmdproject',
            options={'ordering': ('short_name',), 'verbose_name': 'GCMD Project'},
        ),
        migrations.RenameField(
            model_name='gcmdplatform',
            old_name='category',
            new_name='basis',
        ),
        migrations.RenameField(
            model_name='gcmdplatform',
            old_name='series_entry',
            new_name='crazynewcategory',
        ),
        migrations.AddField(
            model_name='gcmdplatform',
            name='subcategory',
            field=models.CharField(blank=True, default='', max_length=256),
        ),
    ]
