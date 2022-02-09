# Generated by Django 3.1.3 on 2021-03-31 21:12

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ("data_models", "0032_auto_20210331_1504"),
    ]

    operations = [
        migrations.RenameField(
            model_name="campaignwebsite",
            old_name="priority",
            new_name="order_priority",
        ),
        migrations.AlterUniqueTogether(
            name="campaignwebsite",
            unique_together={("campaign", "order_priority"), ("campaign", "website")},
        ),
    ]
