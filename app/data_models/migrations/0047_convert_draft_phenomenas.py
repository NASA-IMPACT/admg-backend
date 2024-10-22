from django.db import migrations
from api_app.models import Change


def convert_phenomenas_to_phenomena(apps, schema_editor):
    instrument_drafts = Change.objects.filter(content_type__model="instrument")
    for instrument_draft in instrument_drafts:
        try:
            instrument_draft.update['gcmd_phenomena'] = instrument_draft.update.pop(
                'gcmd_phenomenas'
            )
            instrument_draft.save(post_save=True)
        except KeyError:
            pass


class Migration(migrations.Migration):
    dependencies = [
        ("data_models", "0046_auto_20220526_1047"),
        ("api_app", "0015_change_field_status_tracking"),
    ]

    operations = [
        migrations.RunPython(
            convert_phenomenas_to_phenomena, reverse_code=migrations.RunPython.noop
        )
    ]
