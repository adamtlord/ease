# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2018-02-26 04:39
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0021_auto_20180201_2148'),
        ('concierge', '0006_auto_20171103_1053'),
    ]

    operations = [
        migrations.AddField(
            model_name='touch',
            name='group',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='billing.GroupMembership'),
        ),
    ]
