# Generated by Django 3.1.3 on 2022-11-08 18:33

from django.db import migrations


def set_updated_at(apps, schema_editor):
    Change = apps.get_model("api_app", "Change")
    ApprovalLog = apps.get_model("api_app", "ApprovalLog")

    for change in Change.objects.all():
        Change.objects.filter(pk=change.pk).update(
            updated_at=ApprovalLog.objects.filter(change=change).order_by("-date").first().date
        )


class Migration(migrations.Migration):

    dependencies = [
        ('api_app', '0017_change_updated_at'),
    ]

    operations = [migrations.RunPython(set_updated_at)]
