# Generated by Django 3.1.3 on 2021-03-05 20:49

from django.db import migrations


class Migration(migrations.Migration):
    dependencies = [
        ("api_app", "0012_merge_20210301_1801"),
    ]

    operations = [
        migrations.AlterModelOptions(
            name="approvallog",
            options={"ordering": ["-date"]},
        ),
    ]