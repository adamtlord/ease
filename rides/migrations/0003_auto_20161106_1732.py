# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-11-06 17:32
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0003_auto_20161106_0022'),
        ('rides', '0002_auto_20161106_0022'),
    ]

    operations = [
        migrations.AlterUniqueTogether(
            name='destination',
            unique_together=set([('home', 'customer')]),
        ),
    ]