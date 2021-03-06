# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2017-08-24 03:10
from __future__ import unicode_literals

from django.db import migrations, models


def convert_inactive_users_to_inactive_customers(apps, schema_editor):
    CustomUser = apps.get_model('accounts', 'CustomUser')
    inactive_users = CustomUser.objects.filter(is_active=False)
    for user in inactive_users:
        try:
            user.is_active = True
            user.customer.is_active = False
            user.save()
            user.customer.save()
        except CustomUser.customer.RelatedObjectDoesNotExist:
            pass


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0026_userprofile_source_specific'),
    ]

    operations = [
        migrations.AddField(
            model_name='customer',
            name='is_active',
            field=models.BooleanField(default=True, help_text='Designates whether this customer should be treated as active.', verbose_name='active'),
        ),
        migrations.RunPython(convert_inactive_users_to_inactive_customers),
    ]
