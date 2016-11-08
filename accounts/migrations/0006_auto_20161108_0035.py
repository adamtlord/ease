# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-11-08 00:35
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('rides', '0005_auto_20161108_0029'),
        ('accounts', '0005_auto_20161108_0029'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customerprofile',
            name='most_recent_ride',
        ),
        migrations.AddField(
            model_name='customerprofile',
            name='last_ride',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='last_ride', to='rides.Ride'),
        ),
    ]