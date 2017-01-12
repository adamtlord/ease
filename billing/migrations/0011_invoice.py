# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-01-03 19:08
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0017_remove_customer_last_ride'),
        ('billing', '0010_auto_20161206_1617'),
    ]

    operations = [
        migrations.CreateModel(
            name='Invoice',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('stripe_id', models.CharField(max_length=255)),
                ('created_date', models.DateTimeField(blank=True, null=True)),
                ('invoiced', models.BooleanField(default=False)),
                ('invoiced_date', models.DateTimeField(blank=True, null=True)),
                ('paid', models.BooleanField(default=False)),
                ('paid_date', models.DateTimeField(blank=True, null=True)),
                ('customer', models.ForeignKey(on_delete=django.db.models.deletion.CASCADE, related_name='invoices', to='accounts.Customer')),
            ],
        ),
    ]