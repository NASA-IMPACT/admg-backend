# Generated by Django 3.1.3 on 2021-01-19 03:49

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('api_app', '0005_auto_20201026_1622'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='change',
            options={'verbose_name': 'Draft'},
        ),
        migrations.AlterField(
            model_name='change',
            name='action',
            field=models.CharField(choices=[('Create', 'Create'), ('Update', 'Update'), ('Delete', 'Delete'), ('Patch', 'Patch')], default='Update', max_length=10),
        ),
        migrations.AlterField(
            model_name='change',
            name='appr_reject_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.DO_NOTHING, related_name='approved_by', to=settings.AUTH_USER_MODEL),
        ),
        migrations.AlterField(
            model_name='change',
            name='appr_reject_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AlterField(
            model_name='change',
            name='content_type',
            field=models.ForeignKey(help_text='Model for which the draft pertains.', on_delete=django.db.models.deletion.CASCADE, to='contenttypes.contenttype'),
        ),
        migrations.AlterField(
            model_name='change',
            name='previous',
            field=models.JSONField(default=dict),
        ),
        migrations.AlterField(
            model_name='change',
            name='status',
            field=models.IntegerField(choices=[(2, 'Pending'), (3, 'Approved'), (1, 'In Progress')], default=1),
        ),
        migrations.AlterField(
            model_name='change',
            name='update',
            field=models.JSONField(blank=True, default=dict),
        ),
        migrations.AlterField(
            model_name='change',
            name='user',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.SET_NULL, related_name='changed_by', to=settings.AUTH_USER_MODEL),
        ),
    ]
