from __future__ import unicode_literals

from django.db import models
from localflavor.us.models import PhoneNumberField, USStateField, USZipCodeField


class Location(models.Model):
    name = models.CharField(max_length=50, blank=True, null=True)
    street1 = models.CharField(max_length=100, blank=True, null=True)
    street2 = models.CharField(max_length=100, blank=True, null=True)
    city = models.CharField(max_length=100, blank=True, null=True)
    state = USStateField(blank=True, null=True)
    zip_code = USZipCodeField(blank=True, null=True)
    country = models.CharField(max_length=100, blank=True, null=True, default="U.S.A.")
    phone = PhoneNumberField(blank=True, null=True)

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.name
