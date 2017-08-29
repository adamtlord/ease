# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-08-28 23:54
from __future__ import unicode_literals

from django.conf import settings
from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        migrations.swappable_dependency(settings.AUTH_USER_MODEL),
        ('concierge', '0004_auto_20170823_1959'),
    ]

    operations = [
        migrations.AddField(
            model_name='touch',
            name='concierge',
            field=models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to=settings.AUTH_USER_MODEL),
        ),
    ]
