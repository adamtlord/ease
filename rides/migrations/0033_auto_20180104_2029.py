# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2018-01-05 04:29
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('rides', '0032_destination_address_for_gps'),
    ]

    operations = [
        migrations.AlterField(
            model_name='destination',
            name='address_for_gps',
            field=models.CharField(blank=True, help_text='If a different address drops a better pin, use it instead', max_length=512, null=True, verbose_name='Alternative address for GPS'),
        ),
    ]