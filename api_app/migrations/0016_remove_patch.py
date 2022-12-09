from django.db import migrations, models
from api_app.models import Change


def transition_patch_to_update(apps, schema_editor):
    Change.objects.filter(action='Patch').update(action=Change.Actions.UPDATE)


class Migration(migrations.Migration):

    dependencies = [('api_app', '0015_change_field_status_tracking')]

    operations = [
        migrations.RunPython(transition_patch_to_update, reverse_code=migrations.RunPython.noop),
        migrations.AlterField(
            model_name='change',
            name='action',
            field=models.CharField(
                choices=[('Create', 'Create'), ('Update', 'Update'), ('Delete', 'Delete')],
                default='Update',
                max_length=10,
            ),
        ),
    ]