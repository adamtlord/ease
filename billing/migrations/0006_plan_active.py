# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-11-29 22:42
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0005_auto_20161129_1034'),
    ]

    operations = [
        migrations.AddField(
            model_name='plan',
            name='active',
            field=models.BooleanField(default=True),
        ),
    ]
