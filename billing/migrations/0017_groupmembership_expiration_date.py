# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-04-03 22:29
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0016_groupmembership_bill_online'),
    ]

    operations = [
        migrations.AddField(
            model_name='groupmembership',
            name='expiration_date',
            field=models.DateField(blank=True, null=True),
        ),
    ]
