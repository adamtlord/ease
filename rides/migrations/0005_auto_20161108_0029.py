# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-11-08 00:29
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0005_auto_20161108_0029'),
        ('rides', '0004_auto_20161106_1848'),
    ]

    operations = [
        migrations.CreateModel(
            name='Ride',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('start_date', models.DateTimeField(blank=True, null=True)),
                ('end_date', models.DateTimeField(blank=True, null=True)),
                ('cost', models.DecimalField(blank=True, decimal_places=2, max_digits=9, null=True)),
                ('distance', models.DecimalField(blank=True, decimal_places=4, max_digits=9, null=True)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, to='accounts.CustomerProfile')),
            ],
        ),
        migrations.AlterField(
            model_name='destination',
            name='name',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AlterField(
            model_name='destination',
            name='nickname',
            field=models.CharField(blank=True, max_length=50, null=True),
        ),
        migrations.AddField(
            model_name='ride',
            name='destination',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='ending_point', to='rides.Destination'),
        ),
        migrations.AddField(
            model_name='ride',
            name='start',
            field=models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='starting_point', to='rides.Destination'),
        ),
    ]