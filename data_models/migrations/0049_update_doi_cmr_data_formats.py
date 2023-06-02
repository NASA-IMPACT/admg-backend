from django.db import migrations, models
from api_app.models import Change
import json


def convert_data_format_to_json(apps, schema_editor):
    # there are no published DOIs which have this data, however there are drafts which need to be converted
    doi_drafts = Change.objects.filter(content_type__model="doi")
    for doi_draft in doi_drafts:
        if 'cmr_data_formats' in doi_draft.update.keys():
            doi_draft.update['cmr_data_formats'] = json.dumps(doi_draft.update['cmr_data_formats'])
            doi_draft.save(post_save=True)


class Migration(migrations.Migration):
    dependencies = [('data_models', '0048_convert_draft_phenomenas_previous')]

    operations = [
        # cmr_data_formats can't be directly converted, must be removed and readded
        # no data is currently in cmr_data_formats for published DOIs, so this is not a problem
        migrations.RemoveField(model_name='doi', name='cmr_data_formats'),
        migrations.AddField(
            model_name='doi',
            name='cmr_data_formats',
            field=models.JSONField(blank=True, default=None, null=True),
        ),
        migrations.RunPython(convert_data_format_to_json, reverse_code=migrations.RunPython.noop),
    ]
