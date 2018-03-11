# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2018-02-26 04:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0032_customuser_is_group_admin'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customuser',
            name='is_group_admin',
            field=models.BooleanField(default=False, help_text='Designates whether the user is the administrator of a Group Membership.'),
        ),
    ]