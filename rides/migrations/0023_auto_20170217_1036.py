# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-02-17 18:36
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('rides', '0022_ride_fees'),
    ]

    operations = [
        migrations.RenameField(
            model_name='ride',
            old_name='fee',
            new_name='arrive_fee',
        ),
    ]
