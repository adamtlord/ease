from __future__ import unicode_literals

from django.db import models
from django.utils import formats

from common.models import Location
from common.utils import geocode_address, get_distance

from rides.managers import RidesInProgressManager, RidesReadyToBillManager, RidesIncompleteManager
from rides.const import SERVICES, UBER, LYFT


class Destination(Location):
    nickname = models.CharField(max_length=50, blank=True, null=True)
    customer = models.ForeignKey('accounts.Customer')
    home = models.BooleanField(default=False)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)

    @property
    def ltlng(self):
        return '{},{}'.format(self.latitude, self.longitude)

    def save(self, *args, **kwargs):
        super(Destination, self).save(*args, **kwargs)
        if not (self.latitude and self.longitude):
            address_string = '{} {} {} {}'.format(self.street1, self.city, self.state, self.zip_code)
            try:
                ltlng = geocode_address(address_string)
                self.latitude = ltlng[0]
                self.longitude = ltlng[1]
            except Exception:
                pass
            super(Destination, self).save(*args, **kwargs)

    @property
    def fullname(self):
        if self.name and self.nickname:
            return '{} ({})'.format(self.nickname, self.name)
        else:
            return self.name if self.name else self.nickname

    @property
    def display_name(self):
        return '{}, {}'.format(self.fullname, self.street1)

    @property
    def fulladdress(self):
        street2 = ' {}'.format(self.street2) if self.street2 else ''
        return '{}{} {} {} {}'.format(self.street1, street2, self.city, self.state, self.zip_code)

    def __unicode__(self):
        if self.name and self.nickname:
            return '{} ({}) - {}'.format(self.nickname, self.name, self.customer)
        else:
            return '{} - {}'.format(self.name, self.customer)


class Ride(models.Model):
    customer = models.ForeignKey('accounts.Customer')
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    request_time = models.DateTimeField(blank=True, null=True)
    start = models.ForeignKey('rides.Destination', related_name='starting_point', verbose_name='Starting point')
    destination = models.ForeignKey('rides.Destination', related_name='ending_point')
    cost = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=9)
    fare_estimate = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=9)
    distance = models.DecimalField(blank=True, null=True, decimal_places=4, max_digits=9)
    service = models.CharField(max_length=64, blank=True, null=True, choices=SERVICES, default=LYFT)
    external_id = models.CharField(max_length=64, blank=True, null=True)
    complete = models.BooleanField(default=False)
    invoiced = models.BooleanField(default=False)
    invoiced_date = models.DateTimeField(blank=True, null=True)
    paid = models.BooleanField(default=False)
    paid_date = models.DateTimeField(blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    fee = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=9)
    total_cost = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=9)

    objects = models.Manager()
    in_progress = RidesInProgressManager()
    ready_to_bill = RidesReadyToBillManager()
    incomplete = RidesIncompleteManager()

    @property
    def is_complete(self):
        return self.cost and self.end_date

    @property
    def description(self):
        return '{} - {} to {}'.format(formats.date_format(self.start_date, "SHORT_DATETIME_FORMAT"), self.start.street1, self.destination.street1)

    def save(self, *args, **kwargs):
        super(Ride, self).save(*args, **kwargs)
        if self.start and self.destination and not self.distance:
            try:
                distance = get_distance(self)
                self.distance = round(distance, 4)
            except Exception:
                pass
            super(Ride, self).save(*args, **kwargs)

    def __unicode__(self):
        if self.customer:
            return '{} from {} to {}'.format(self.customer, self.start.fullname, self.destination.fullname)


class Notification(models.Model):
    customer = models.ForeignKey('accounts.Customer')
    rider = models.ForeignKey('accounts.Rider', blank=True, null=True)
    ride = models.ForeignKey(Ride)
    lovedone = models.ForeignKey('accounts.LovedOne')
    sent = models.DateTimeField(blank=True, null=True)
