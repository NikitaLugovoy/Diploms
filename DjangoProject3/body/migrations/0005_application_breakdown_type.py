# Generated by Django 5.1.3 on 2025-03-04 10:33

import django.db.models.deletion
from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('body', '0004_breakdowntype'),
    ]

    operations = [
        migrations.AddField(
            model_name='application',
            name='breakdown_type',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='applications', to='body.breakdowntype'),
        ),
    ]
