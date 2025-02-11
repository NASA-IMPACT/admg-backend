# Generated by Django 3.1.3 on 2022-08-12 22:41

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):
    dependencies = [
        ('contenttypes', '0002_remove_content_type_name'),
        ('api_app', '0015_change_field_status_tracking'),
    ]

    operations = [
        migrations.AlterField(
            model_name='change',
            name='action',
            field=models.CharField(
                choices=[('Create', 'Create'), ('Update', 'Update'), ('Delete', 'Delete')],
                default='Update',
                max_length=10,
            ),
        ),
        migrations.CreateModel(
            name='Recommendation',
            fields=[
                (
                    'id',
                    models.AutoField(
                        auto_created=True, primary_key=True, serialize=False, verbose_name='ID'
                    ),
                ),
                ('object_uuid', models.UUIDField()),
                (
                    'result',
                    models.BooleanField(null=True, verbose_name='Was the CASEI object connected?'),
                ),
                (
                    'submitted',
                    models.BooleanField(
                        default=False, verbose_name='Has the user published their result?'
                    ),
                ),
                (
                    'change',
                    models.ForeignKey(
                        on_delete=django.db.models.deletion.CASCADE, to='api_app.change'
                    ),
                ),
                (
                    'content_type',
                    models.ForeignKey(
                        blank=True,
                        on_delete=django.db.models.deletion.CASCADE,
                        to='contenttypes.contenttype',
                    ),
                ),
            ],
        ),
        migrations.AddConstraint(
            model_name='recommendation',
            constraint=models.UniqueConstraint(
                fields=('change', 'object_uuid'), name='unique_recommendation'
            ),
        ),
    ]
