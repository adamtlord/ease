from __future__ import unicode_literals

from django.db import models

from common.models import Location
from common.utils import geocode_address


class Destination(Location):
    nickname = models.CharField(max_length=50, blank=True, null=True)
    customer = models.ForeignKey('accounts.Customer')
    home = models.BooleanField(default=False)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)

    @property
    def ltlng(self):
        return '{},{}'.format(self.lattitude, self.longitute)

    def save(self, *args, **kwargs):
        super(Destination, self).save(*args, **kwargs)
        if not (self.latitude and self.longitude):
            address_string = '{} {} {} {} {}'.format(self.street1, self.street2, self.city, self.state, self.zip_code)
            try:
                ltlng = geocode_address(address_string)
                self.latitude = ltlng[0]
                self.longitude = ltlng[1]
            except Exception:
                pass
            super(Destination, self).save(*args, **kwargs)

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
