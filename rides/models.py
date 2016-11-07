from __future__ import unicode_literals

from django.db import models

from common.models import Location


class Destination(Location):
    nickname = models.CharField(max_length=50, blank=True, null=True)
    customer = models.ForeignKey('accounts.CustomerProfile')
    home = models.BooleanField(default=False)

    def __unicode__(self):
        if self.name and self.nickname:
            return '{} ({}) - {}'.format(self.nickname, self.name, self.customer)
        else:
            return '{} - {}'.format(self.name, self.customer)
