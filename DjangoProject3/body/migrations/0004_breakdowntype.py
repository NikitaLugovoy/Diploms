# Generated by Django 5.1.3 on 2025-03-04 10:24

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('body', '0003_schedule'),
    ]

    operations = [
        migrations.CreateModel(
            name='BreakdownType',
            fields=[
                ('id', models.BigAutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('name', models.CharField(max_length=255, unique=True)),
            ],
            options={
                'db_table': 'breakdown_types',
            },
        ),
    ]
