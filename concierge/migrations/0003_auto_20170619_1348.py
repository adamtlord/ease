# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-06-19 20:48
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('concierge', '0002_auto_20161209_1442'),
    ]

    operations = [
        migrations.AlterField(
            model_name='touch',
            name='customer',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='accounts.Customer'),
        ),
    ]
