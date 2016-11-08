from __future__ import unicode_literals

from django.db import models

from common.models import Location


class Contact(models.Model):
    first_name = models.CharField(max_length=50)
    last_name = models.CharField(max_length=50)
    email = models.EmailField(blank=True, null=True)

    class Meta:
        abstract = True

    def __unicode__(self):
        return '{} {}'.format(self.first_name, self.last_name)


class Customer(Contact):
    APARTMENT = 'AP'
    ASSISTED_LIVING = 'AL'
    RETIREMENT_COMMUNITY = 'RT'
    SINGLE_FAMILY_HOME = 'SF'
    SKILLED_NURSING = 'SN'

    RESIDENCE_TYPE_CHOICES = (
        (APARTMENT, 'Apartment'),
        (ASSISTED_LIVING, 'Assisted Living Facility'),
        (RETIREMENT_COMMUNITY, 'Retirement Community'),
        (SINGLE_FAMILY_HOME, 'Single Family Home'),
        (SKILLED_NURSING, 'Skilled Nursing Facility'),
    )

    known_as = models.CharField(max_length=50, blank=True, null=True)
    date_joined = models.DateField(auto_now_add=True)
    dob = models.DateField(blank=True, null=True, verbose_name="Date of birth")
    last_ride = models.ForeignKey('rides.Ride', blank=True, null=True, related_name='last_ride')
    spent_to_date = models.DecimalField(blank=True, null=True, decimal_places=2, max_digits=9)
    residence_type = models.CharField(max_length=2, choices=RESIDENCE_TYPE_CHOICES, default=SINGLE_FAMILY_HOME)
    residence_instructions = models.TextField(blank=True, null=True)
    special_assistance = models.CharField(max_length=1024, blank=True, null=True)
    notes = models.TextField(blank=True, null=True)

    @property
    def home(self):
        return self.destination_set.filter(home=True).first()

    @property
    def destinations(self):
        return self.destination_set.exclude(home=True)


class LovedOne(Contact, Location):
    customer = models.ForeignKey(Customer)
    relationship = models.CharField(max_length=100, blank=True, null=True)
    text_updates = models.BooleanField(default=False)
