# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-11-06 18:48
from __future__ import unicode_literals

from django.db import migrations, models
import localflavor.us.models


class Migration(migrations.Migration):

    dependencies = [
        ('rides', '0003_auto_20161106_1732'),
    ]

    operations = [
        migrations.AlterField(
            model_name='destination',
            name='name',
            field=models.CharField(blank=True, help_text='e.g., Dunder Mifflin Scranton', max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='destination',
            name='nickname',
            field=models.CharField(blank=True, help_text='e.g., My paper supplier', max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='destination',
            name='street1',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Address 1'),
        ),
        migrations.AlterField(
            model_name='destination',
            name='street2',
            field=models.CharField(blank=True, max_length=100, null=True, verbose_name='Address 2'),
        ),
        migrations.AlterField(
            model_name='destination',
            name='zip_code',
            field=localflavor.us.models.USZipCodeField(blank=True, null=True, verbose_name='ZIP'),
        ),
        migrations.AlterUniqueTogether(
            name='destination',
            unique_together=set([]),
        ),
    ]
