from __future__ import unicode_literals

from django.db import models
from django.utils import formats, timezone

from common.models import Location
from common.utils import geocode_address

from rides.managers import RidesInProgressManager, RidesReadyToBillManager, RidesIncompleteManager
from rides.const import COMPANIES, UBER, LYFT
from billing.models import Invoice


class Destination(Location):
    nickname = models.CharField(max_length=50, blank=True, null=True)
    customer = models.ForeignKey('accounts.Customer')
    home = models.BooleanField(default=False)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    included_in_plan = models.BooleanField(default=False)

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
        if self.home:
            name = 'Home'
        else:
            name = self.name
        if name and self.nickname:
            return '{} ({})'.format(self.nickname, name)
        else:
            return name if name else self.nickname

    @property
    def display_name(self):
        return '{}, {}'.format(self.fullname, self.street1)

    @property
    def fulladdress(self):
        street2 = ' {}'.format(self.street2) if self.street2 else ''
        return '{}{} {} {} {}'.format(self.street1, street2, self.city, self.state, self.zip_code)

    def __unicode__(self):
        return '{} - {}'.format(self.fullname, self.customer)


class Ride(models.Model):
    customer = models.ForeignKey('accounts.Customer')
    start_date = models.DateTimeField(blank=True, null=True)
    end_date = models.DateTimeField(blank=True, null=True)
    request_time = models.DateTimeField(blank=True, null=True)
    start = models.ForeignKey('rides.Destination', related_name='starting_point', verbose_name='Starting point', on_delete=models.SET_NULL, null=True)
    destination = models.ForeignKey('rides.Destination', related_name='ending_point', on_delete=models.SET_NULL, null=True)
    cost = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=9)
    fare_estimate = models.CharField(max_length=128, blank=True, null=True)
    distance = models.DecimalField(blank=True, null=True, decimal_places=4, max_digits=9)
    company = models.CharField(max_length=64, blank=True, null=True, choices=COMPANIES)
    external_id = models.CharField(max_length=64, blank=True, null=True)
    complete = models.BooleanField(default=False)
    invoice_item_id = models.CharField(max_length=64, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    fee = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=9)
    total_cost = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=9)
    included_in_plan = models.BooleanField(default=False)
    invoice = models.ForeignKey(Invoice, related_name="rides", blank=True, null=True)
    invoiced = models.BooleanField(default=False)

    objects = models.Manager()
    in_progress = RidesInProgressManager()
    ready_to_bill = RidesReadyToBillManager()
    incomplete = RidesIncompleteManager()

    class Meta:
        ordering = ['-start_date']

    @property
    def is_complete(self):
        return self.cost or self.complete

    @property
    def description(self):
        startstreet = destinationstreet = ''
        if self.start.street1:
            startstreet = self.start.street1
        if self.destination.street1:
            destinationstreet = self.destination.street1
        return '{} - {} to {}'.format(formats.date_format(self.start_date, "SHORT_DATETIME_FORMAT"), startstreet, destinationstreet)

    @property
    def total_cost_estimate(self):
        if self.cost:
            if self.included_in_plan:
                return 0
            else:
                return self.cost + self.customer.plan.arrive_fee
        return None

    @property
    def is_scheduled(self):
        return self.start_date > timezone.now()

    def __unicode__(self):
        if self.start:
            start = self.start.fullname
        else:
            start = '[NONE]'
        if self.destination:
            destination = self.destination.fullname
        else:
            destination = '[NONE]'
        if self.customer:
            return '{} from {} to {}'.format(self.customer, start, destination)


class Notification(models.Model):
    customer = models.ForeignKey('accounts.Customer')
    rider = models.ForeignKey('accounts.Rider', blank=True, null=True)
    ride = models.ForeignKey(Ride)
    lovedone = models.ForeignKey('accounts.LovedOne')
    sent = models.DateTimeField(blank=True, null=True)
