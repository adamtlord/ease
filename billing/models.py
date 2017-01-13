from __future__ import unicode_literals
import datetime
from django.db import models
from localflavor.us.models import USZipCodeField

from common.models import AbstractEnumModel


class Plan(AbstractEnumModel):

    BRONZE = 1
    SILVER = 2
    GOLD = 3
    INTRO_GIFT = 4

    CHOICES = (
        (BRONZE, 'Bronze Membership'),
        (SILVER, 'Silver Membership'),
        (GOLD, 'Gold Membership'),
        (INTRO_GIFT, 'Unlimited Gift Certificate'),
    )

    active = models.BooleanField(default=True)
    public = models.BooleanField(default=True)
    unlimited_rides = models.BooleanField(default=False)
    included_rides_per_month = models.PositiveSmallIntegerField(blank=True, null=True, help_text="Number of rides per month included in plan. Additional rides will be billed to customer.")
    ride_distance_limit = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=6, help_text="Limit, in miles, of rides included in this plan.")
    monthly_cost = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=6, help_text="The monthly subscription fee for this plan, in dollars.")
    signup_cost = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=6, help_text="A one-time fee charged on signup. Not required.")
    arrive_fee = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=6, help_text="The Arrive surcharge added to rides not included in the plan, in dollars.")
    stripe_id = models.CharField(blank=True, null=True, max_length=128)

    def is_active(self):
        return self.active

    @property
    def is_gift(self):
        return self.id == self.INTRO_GIFT

    @property
    def includes_rides(self):
        return self.included_rides_per_month > 0

    def __unicode__(self):
        return self.name


class StripeCustomer(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(blank=True, null=True)
    stripe_id = models.CharField(max_length=255)
    last_4_digits = models.CharField(max_length=4)
    billing_zip = USZipCodeField(blank=True, null=True, verbose_name="Billing zip code")

    def __unicode__(self):
        return '{} {}'.format(self.first_name, self.last_name)


class Invoice(models.Model):
    stripe_id = models.CharField(max_length=255)
    customer = models.ForeignKey('accounts.Customer', related_name="invoices")
    created_date = models.DateTimeField(blank=True, null=True)
    invoiced = models.BooleanField(default=False)
    invoiced_date = models.DateTimeField(blank=True, null=True)
    paid = models.BooleanField(default=False)
    paid_date = models.DateTimeField(blank=True, null=True)
    period_start = models.DateTimeField(blank=True, null=True)
    period_end = models.DateTimeField(blank=True, null=True)
    attempt_count = models.PositiveSmallIntegerField(blank=True, null=True)
    total = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=6)

    def __unicode__(self):
        return '{} {}'.format(self.customer, self.stripe_id)
