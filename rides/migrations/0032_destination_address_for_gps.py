# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2018-01-02 04:48
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rides', '0031_auto_20171107_1626'),
    ]

    operations = [
        migrations.AddField(
            model_name='destination',
            name='address_for_gps',
            field=models.CharField(blank=True, max_length=512, null=True),
        ),
    ]
