# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-08-24 02:59
from __future__ import unicode_literals

from django.db import migrations


class Migration(migrations.Migration):

    dependencies = [
        ('concierge', '0003_auto_20170619_1348'),
    ]

    operations = [
        migrations.AlterModelOptions(
            name='touch',
            options={'ordering': ['-date'], 'verbose_name': 'Touch', 'verbose_name_plural': 'Touches'},
        ),
    ]