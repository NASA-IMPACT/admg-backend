# Generated by Django 2.2.3 on 2020-10-26 21:22

from django.db import migrations, models
import django.db.models.deletion


def populate_content_type(apps, schema_editor):
    Change = apps.get_model("api_app", "Change")
    ContentType = apps.get_model("contenttypes", "ContentType")
    for model_name in Change.objects.values_list("model_name", flat=True).distinct():
        Change.objects.filter(model_name=model_name).update(
            content_type=ContentType.objects.get(app_label="data_models", model=model_name.lower())
        )


def noop(apps, schema_editor):
    pass


class Migration(migrations.Migration):
    dependencies = [
        ("contenttypes", "0002_remove_content_type_name"),
        ("api_app", "0004_auto_20200409_1912"),
        ("data_models", "0006_auto_20201009_0715"),
    ]

    operations = [
        migrations.AddField(
            model_name="change",
            name="content_type",
            field=models.ForeignKey(
                null=True,
                on_delete=django.db.models.deletion.CASCADE,
                to="contenttypes.ContentType",
            ),
            preserve_default=False,
        ),
        migrations.RunPython(populate_content_type, noop),
        migrations.AlterField(
            model_name="change",
            name="content_type",
            field=models.ForeignKey(
                on_delete=django.db.models.deletion.CASCADE,
                to="contenttypes.ContentType",
            ),
            preserve_default=False,
        ),
        migrations.RemoveField(model_name="change", name="model_name"),
    ]