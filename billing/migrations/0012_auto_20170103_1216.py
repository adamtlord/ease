# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-01-03 20:16
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0011_invoice'),
    ]

    operations = [
        migrations.AddField(
            model_name='invoice',
            name='attempt_count',
            field=models.PositiveSmallIntegerField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='invoice',
            name='period_end',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='invoice',
            name='period_start',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='invoice',
            name='total',
            field=models.DecimalField(blank=True, decimal_places=2, max_digits=6, null=True),
        ),
    ]
