# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-12-07 00:17
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rides', '0008_ride_request_time'),
    ]

    operations = [
        migrations.AddField(
            model_name='ride',
            name='invoiced_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
        migrations.AddField(
            model_name='ride',
            name='paid_date',
            field=models.DateTimeField(blank=True, null=True),
        ),
    ]