# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-02-06 19:09
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0018_userprofile_phone'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='customer',
            name='send_updates',
        ),
    ]
