from __future__ import unicode_literals

import pytz
import datetime
from django.conf import settings
from django.db import models
from django.utils import timezone
from django.utils.functional import cached_property

from common.models import Location
from common.utils import geocode_address, get_timezone

from rides.managers import RidesInProgressManager, RidesReadyToBillManager, RidesIncompleteManager, ActiveRidesManager
from rides.const import COMPANIES, UBER, LYFT
from billing.models import Invoice, Plan


class Destination(Location):
    added_by = models.ForeignKey('accounts.CustomUser', blank=True, null=True)
    customer = models.ForeignKey('accounts.Customer')
    home = models.BooleanField(default=False)
    included_in_plan = models.BooleanField(default=False)
    latitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    longitude = models.DecimalField(max_digits=9, decimal_places=6, blank=True, null=True)
    nickname = models.CharField(max_length=50, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)
    timezone = models.CharField(max_length=128, blank=True, null=True)
    address_for_gps = models.CharField(max_length=512, blank=True, null=True, verbose_name='Alternative address for GPS', help_text='If a different address drops a better pin, use it instead')

    class Meta:
        ordering = ['name']

    @cached_property
    def ltlng(self):
        return '{},{}'.format(self.latitude, self.longitude)

    def set_ltlng(self):
        address_string = '{} {} {} {}'.format(self.street1, self.city, self.state, self.zip_code)
        try:
            ltlng = geocode_address(address_string)
            self.latitude = ltlng[0]
            self.longitude = ltlng[1]
        except:
            pass

    def set_customer_timezone(self):
        if self.zip_code and self.customer:
            try:
                ltlng = geocode_address(self.zip_code)
                tz_name = get_timezone(ltlng)
                self.customer.timezone = tz_name
                self.customer.save()
            except:
                pass

    def set_timezone(self):
        if self.zip_code:
            try:
                ltlng = geocode_address(self.zip_code)
                tz_name = get_timezone(ltlng)
                self.timezone = tz_name
            except:
                pass
        else:
            try:
                tz_name = get_timezone(self.ltlng)
                self.timezone = tz_name
            except:
                pass

    def save(self, *args, **kwargs):
        super(Destination, self).save(*args, **kwargs)
        if not (self.latitude and self.longitude):
            try:
                self.set_ltlng()
            except:
                pass
        if not self.timezone:
            try:
                self.set_timezone()
            except:
                pass
        super(Destination, self).save(*args, **kwargs)

    @cached_property
    def fullname(self):
        if self.home and not self.name:
            return 'Home'
        if self.name:
            name = self.name
            if name and self.nickname:
                return u'{} ({})'.format(self.nickname, name)
            else:
                return name
        else:
            if self.nickname:
                return self.nickname
            else:
                return self.street1

    @cached_property
    def display_name(self):
        return '{}, {}'.format(self.fullname, self.street1)

    @cached_property
    def fulladdress(self):
        street2 = ' {}'.format(self.street2) if self.street2 else ''
        return '{}{} {} {} {}'.format(self.street1, street2, self.city, self.state, self.zip_code)

    @cached_property
    def tz(self):
        tz_abbrev = ''
        if self.timezone:
            tz = pytz.timezone(self.timezone)
            day = tz.localize(datetime.datetime.now(), is_dst=None)
            tz_abbrev = day.tzname()
        return tz_abbrev

    def __unicode__(self):
        return '{} - {}'.format(self.fullname, self.customer)


class Ride(models.Model):
    added_by = models.ForeignKey('accounts.CustomUser', blank=True, null=True, related_name='added_by')
    arrive_fee = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=9)
    cancelled = models.BooleanField(default=False)
    cancelled_by = models.ForeignKey('accounts.CustomUser', blank=True, null=True, related_name='cancelled_by')
    cancelled_reason = models.CharField(max_length=256, blank=True, null=True)
    company = models.CharField(max_length=64, blank=True, null=True, choices=COMPANIES)
    complete = models.BooleanField(default=False)
    cost = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=9)
    customer = models.ForeignKey('accounts.Customer', related_name='rides')
    destination = models.ForeignKey('rides.Destination', related_name='ending_point', on_delete=models.SET_NULL, null=True)
    distance = models.DecimalField(blank=True, null=True, decimal_places=4, max_digits=9)
    end_date = models.DateTimeField(blank=True, null=True)
    external_id = models.CharField(max_length=64, blank=True, null=True)
    fare_estimate = models.CharField(max_length=128, blank=True, null=True)
    fees = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=9)
    included_in_plan = models.BooleanField(default=False)
    invoice = models.ForeignKey(Invoice, related_name="rides", blank=True, null=True)
    invoice_item_id = models.CharField(max_length=64, blank=True, null=True)
    invoiced = models.BooleanField(default=False)
    invoiced_by = models.ForeignKey('accounts.CustomUser', blank=True, null=True, related_name='invoiced_by')
    notes = models.TextField(blank=True, null=True)
    request_time = models.DateTimeField(blank=True, null=True)
    rider = models.CharField(max_length=128, blank=True, null=True)
    rider_link = models.ForeignKey('accounts.Rider', blank=True, null=True)
    start = models.ForeignKey('rides.Destination', related_name='starting_point', verbose_name='Starting point', on_delete=models.SET_NULL, null=True)
    start_date = models.DateTimeField(blank=True, null=True)
    total_cost = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=9)

    objects = models.Manager()
    in_progress = RidesInProgressManager()
    ready_to_bill = RidesReadyToBillManager()
    incomplete = RidesIncompleteManager()
    active = ActiveRidesManager()

    class Meta:
        ordering = ['-start_date']

    @cached_property
    def get_arrive_fee(self):
        if self.customer.group_membership and self.customer.group_membership.includes_arrive_fee:
            return self.customer.group_membership.plan.arrive_fee
        if self.included_in_plan:
            return 0
        if self.customer.plan:
            # for accurate records, if the plan's arrive_fee was increased on 1/1/2018, show the old fee
            if self.customer.plan.id in [Plan.COPPER, Plan.BRONZE, Plan.GOLD, Plan.SILVER] and self.start_date.year < 2018:
                return 3.0
            return self.customer.plan.arrive_fee or 0
        return 0

    @cached_property
    def get_cost(self):
        if self.included_in_plan:
            return 0
        return self.cost or 0

    @cached_property
    def is_complete(self):
        return self.cost or self.complete

    @cached_property
    def description(self):
        startstreet = destinationstreet = ''
        if self.start.street1:
            startstreet = self.start.street1
        if self.destination.street1:
            destinationstreet = self.destination.street1
        return '{} to {}'.format(startstreet, destinationstreet)

    @cached_property
    def total_fees_estimate(self):
        fees = self.fees or 0
        arrive_fee = self.get_arrive_fee
        return fees + arrive_fee

    @cached_property
    def total_fees(self):
        fees = self.fees or 0
        arrive_fee = self.arrive_fee or 0
        return fees + arrive_fee

    @cached_property
    def total_cost_estimate(self):
        cost = self.get_cost
        return cost + self.total_fees_estimate

    @cached_property
    def is_scheduled(self):
        return self.start_date > timezone.now()

    @cached_property
    def cost_to_group(self):
        cost = 0
        group = self.customer.group_membership
        if not group:
            return cost
        if group.includes_ride_cost:
            cost += self.cost + self.fees
        if group.includes_arrive_fee:
            cost += group.plan.arrive_fee
        return cost

    @property
    def is_today(self):
        tz = pytz.timezone(settings.TIME_ZONE)
        today = timezone.now().astimezone(tz)
        start_date = self.start_date.astimezone(tz)
        return start_date.date() == today.date()

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
