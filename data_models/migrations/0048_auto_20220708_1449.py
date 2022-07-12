# Generated by Django 3.1.3 on 2022-07-08 19:49

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('data_models', '0047_convert_draft_phenomenas'),
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
            old_name='series_entry',
            new_name='subcategory',
        ),
        migrations.RenameField(
            model_name='gcmdplatform',
            old_name='category',
            new_name='basis',
        ),
        migrations.AddField(
            model_name='gcmdplatform',
            name='category',
            field=models.CharField(max_length=256, blank=True, default=""),
            preserve_default=False,
        ),
    ]
