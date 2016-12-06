# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-12-06 22:57
from __future__ import unicode_literals

from django.db import migrations
import localflavor.us.models


class Migration(migrations.Migration):

    dependencies = [
        ('billing', '0008_plan_signup_cost'),
    ]

    operations = [
        migrations.AddField(
            model_name='stripecustomer',
            name='billing_zip',
            field=localflavor.us.models.USZipCodeField(blank=True, null=True, verbose_name='ZIP'),
        ),
    ]