# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-04-28 23:34
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rides', '0025_ride_rider'),
    ]

    operations = [
        migrations.AddField(
            model_name='destination',
            name='unit',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Unit #'),
        ),
    ]
