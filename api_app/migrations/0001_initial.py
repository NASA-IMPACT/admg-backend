# Generated by Django 2.2.3 on 2020-03-12 16:19

from django.db import migrations, models


class Migration(migrations.Migration):

    initial = True

    dependencies = [
    ]

    operations = [
        migrations.CreateModel(
            name='DummyModel',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('test1', models.CharField(blank=True, max_length=15, verbose_name='testing 1')),
                ('test2', models.CharField(max_length=15, verbose_name='testing 2')),
                ('test3', models.IntegerField(verbose_name='testing 3')),
            ],
        ),
    ]
