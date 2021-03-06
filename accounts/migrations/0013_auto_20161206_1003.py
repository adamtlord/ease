# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-12-06 18:03
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0012_auto_20161206_0950'),
    ]

    operations = [
        migrations.AlterField(
            model_name='lovedone',
            name='customer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='lovedones', to='accounts.Customer'),
        ),
        migrations.AlterField(
            model_name='rider',
            name='customer',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='riders', to='accounts.Customer'),
        ),
    ]
