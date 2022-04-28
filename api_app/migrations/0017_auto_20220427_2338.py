# Generated by Django 3.1.3 on 2022-04-28 04:38

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('api_app', '0016_resolvedlog'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='resolvedlog',
            name='content_type',
        ),
        migrations.RemoveField(
            model_name='resolvedlog',
            name='recommended_uuid',
        ),
        migrations.CreateModel(
            name='Recommendation',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('object_uuid', models.UUIDField()),
                ('result', models.BooleanField(blank=True, verbose_name='Was the CASEI object connected?')),
                ('content_type', models.ForeignKey(blank=True, on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype')),
            ],
        ),
    ]
