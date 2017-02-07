# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-02-06 23:14
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0020_customer_send_updates'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='preferred_service',
            field=models.CharField(blank=True, choices=[('Lyft', 'Lyft'), ('UberX', 'UberX'), ('UberXL', 'UberXL'), ('UberASSIST', 'UberASSIST'), ('Other', 'Other')], max_length=16, null=True),
        ),
    ]
