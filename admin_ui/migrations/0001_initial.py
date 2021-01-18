# Generated by Django 3.1.3 on 2020-12-11 16:00

from django.db import migrations, models


def setup_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    User = apps.get_model("users", "User")
    Permission = apps.get_model("auth", "Permission")
    db_alias = schema_editor.connection.alias

    # Editor Group
    editor_group = Group.objects.using(db_alias).create(name="Editor")
    editor_group.permissions.add(
        # R any datamodel
        *Permission.objects.using(db_alias).filter(
            content_type__app_label="data_models", codename__startswith="view_"
        ),
        # CRU Changes
        *Permission.objects.using(db_alias)
        .filter(content_type__app_label="api_app")
        .exclude(codename__startswith="delete_"),
    )
    editor_group.user_set.add(*User.objects.filter(role=2))

    # Admin Group
    admin_group = Group.objects.using(db_alias).create(name="Admin")
    admin_group.permissions.add(
        # CRUD any datamodel
        *Permission.objects.using(db_alias).filter(
            content_type__app_label="data_models"
        ),
        # CRUD Changes
        *Permission.objects.using(db_alias).filter(content_type__app_label="api_app"),
        # CRUD users
        *Permission.objects.using(db_alias).filter(content_type__app_label="users"),
        # Any admin action (e.g. deploy)
        *Permission.objects.using(db_alias).filter(content_type__app_label="admin_ui"),
    )
    admin_group.user_set.add(*User.objects.filter(role=1))


def rm_groups(apps, schema_editor):
    Group = apps.get_model("auth", "Group")
    db_alias = schema_editor.connection.alias
    Group.objects.using(db_alias).filter(name__in=["Admin", "Editor"]).delete()


class Migration(migrations.Migration):

    initial = True

    dependencies = []

    operations = [
        migrations.CreateModel(
            name="AdminPermission",
            fields=[
                (
                    "id",
                    models.AutoField(
                        auto_created=True,
                        primary_key=True,
                        serialize=False,
                        verbose_name="ID",
                    ),
                )
            ],
            options={
                "permissions": (("can_deploy", "Permissions to deploy website"),),
                "managed": False,
                "default_permissions": (),
            },
        ),
        migrations.RunPython(setup_groups, rm_groups),
    ]
