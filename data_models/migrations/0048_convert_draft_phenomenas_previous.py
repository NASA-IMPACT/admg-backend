from django.db import migrations
from api_app.models import Change


def convert_phenomenas_to_phenomena(apps, schema_editor):
    instrument_drafts = Change.objects.filter(content_type__model="instrument")
    for instrument_draft in instrument_drafts:
        if 'gcmd_phenomenas' in instrument_draft.previous.keys():
            instrument_draft.previous['gcmd_phenomena'] = instrument_draft.previous.pop(
                'gcmd_phenomenas'
            )
            instrument_draft.save(post_save=True)


class Migration(migrations.Migration):

    dependencies = [("data_models", "0047_convert_draft_phenomenas")]

    operations = [
        migrations.RunPython(
            convert_phenomenas_to_phenomena, reverse_code=migrations.RunPython.noop
        )
    ]
