# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-11-17 22:24
from __future__ import unicode_literals

from django.db import migrations, models
import django.db.models.deletion


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0031_remove_customer_balance'),
        ('billing', '0020_balance_stripe_customer'),
    ]

    operations = [
        migrations.CreateModel(
            name='Subscription',
            fields=[
                ('id', models.AutoField(auto_created=True, primary_key=True, serialize=False, verbose_name='ID')),
                ('is_active', models.BooleanField(default=False)),
                ('last_billed_date', models.DateField(blank=True, null=True)),
                ('next_billed_date', models.DateField(blank=True, null=True)),
                ('date_created', models.DateField(auto_now_add=True, null=True)),
                ('customer', models.OneToOneField(blank=True, null=True, on_delete=django.db.models.deletion.CASCADE, to='accounts.Customer')),
            ],
        ),
    ]