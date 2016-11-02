from __future__ import unicode_literals

from django.db import models


class Destination(models.Model):
    nickname = models.CharField(max_length=50, blank=True, null=True)
    customer = models.ForeignKey('accounts.CustomerProfile')
    address = models.ForeignKey('common.Location')

    def __unicode__(self):
        nickname = '{}, '.format(self.nickname) if self.nickname else None
        return '{}{}'.format(nickname, self.address.name)
