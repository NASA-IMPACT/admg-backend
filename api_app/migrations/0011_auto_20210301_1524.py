# Generated by Django 3.1.3 on 2021-03-01 21:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('api_app', '0010_auto_20210223_2232'),
    ]

    operations = [
        migrations.AlterField(
            model_name='change',
            name='status',
            field=models.IntegerField(choices=[(0, 'Created'), (1, 'In Progress'), (2, 'In Review'), (3, 'In Admin Review'), (4, 'Published')], default=1),
        ),
    ]