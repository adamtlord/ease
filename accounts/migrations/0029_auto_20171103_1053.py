# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-11-03 17:53
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0028_customer_registered_by'),
    ]

    operations = [
        migrations.AlterField(
            model_name='customer',
            name='registered_by',
            field=models.ForeignKey(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, related_name='registered_by', to=settings.AUTH_USER_MODEL),
        ),
    ]