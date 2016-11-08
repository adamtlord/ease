from __future__ import unicode_literals

from django.db import models

from common.models import Location


class Destination(Location):
    nickname = models.CharField(max_length=50, blank=True, null=True)
    customer = models.ForeignKey('accounts.Customer')
    home = models.BooleanField(default=False)

    def __unicode__(self):
        if self.name and self.nickname:
            return '{} ({}) - {}'.format(self.nickname, self.name, self.customer)
        else:
            return '{} - {}'.format(self.name, self.customer)


class Ride(models.Model):
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    customer = models.ForeignKey('accounts.Customer')
    start = models.ForeignKey('rides.Destination', related_name='starting_point')
    destination = models.ForeignKey('rides.Destination', related_name='ending_point')
    cost = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=9)
    distance = models.DecimalField(blank=True, null=True, decimal_places=4, max_digits=9)
