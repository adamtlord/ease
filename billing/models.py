from __future__ import unicode_literals

from django.db import models

from common.models import AbstractEnumModel


class Plan(AbstractEnumModel):

    BRONZE = 1
    SILVER = 2
    GOLD = 3
    UL_GIFT = 4

    CHOICES = (
        (BRONZE, 'Bronze Membership'),
        (SILVER, 'Silver Membership'),
        (GOLD, 'Gold Membership'),
        (UL_GIFT, 'Unlimited Gift Certificate'),
    )

    active = models.BooleanField(default=True)
    unlimited_rides = models.BooleanField(default=False)
    included_rides_per_month = models.PositiveSmallIntegerField(blank=True, null=True, help_text="Number of rides per month included in plan. Additional rides will be billed to customer.")
    ride_distance_limit = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=6, help_text="Limit, in miles, of rides included in this plan.")
    monthly_cost = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=6, help_text="The monthly subscription fee for this plan, in dollars.")
    signup_cost = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=6, help_text="A one-time fee charged on signup. Not required.")
    arrive_fee = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=6, help_text="The Arrive surcharge added to rides not included in the plan, in dollars.")
    stripe_id = models.CharField(blank=True, null=True, max_length=128)

    def is_active(self):
        return self.active

    def __unicode__(self):
        return self.name


class StripeCustomer(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(blank=True, null=True)
    stripe_id = models.CharField(max_length=255)
    last_4_digits = models.CharField(max_length=4)

    def __unicode__(self):
        return '{} {}'.format(self.first_name, self.last_name)
