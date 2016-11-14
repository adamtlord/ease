# -*- coding: utf-8 -*-
# Generated by Django 1.10.2 on 2016-11-13 23:39
from __future__ import unicode_literals

from django.db import migrations, models


class Migration(migrations.Migration):

    dependencies = [
        ('accounts', '0004_auto_20161113_2112'),
    ]

    operations = [
        migrations.RemoveField(
            model_name='rider',
            name='text_updates',
        ),
        migrations.AddField(
            model_name='rider',
            name='send_updates',
            field=models.PositiveSmallIntegerField(choices=[(1, 'Yes, every time'), (2, 'Yes, on some trips'), (3, 'Not sure'), (0, 'No')], default=0),
        ),
        migrations.AlterField(
            model_name='userprofile',
            name='source',
            field=models.CharField(blank=True, choices=[(None, ''), ('FRIEND_FAMILY', 'Friend or family member'), ('AD_ONLINE', 'Online ad'), ('AD_PRINT', 'Print ad'), ('MEDIA', 'Media or news coverage'), ('OTHER', 'Other')], max_length=255, null=True),
        ),
    ]
