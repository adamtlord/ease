from __future__ import unicode_literals

from django.db import models
from localflavor.us.models import USStateField, USZipCodeField


class AbstractEnumModel(models.Model):
    id = models.IntegerField(primary_key=True)
    name = models.CharField(max_length=64)
    display_name = models.CharField(max_length=128, blank=True, null=True)
    CHOICES = ()

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.name

    def get_dict(self):
        return dict(self.CHOICES)


class Location(models.Model):
    """ An abstract model for storing destinations and addresses """
    name = models.CharField(max_length=50, blank=True, null=True)
    street1 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Address 1")
    street2 = models.CharField(max_length=100, blank=True, null=True, verbose_name="Address 2")
    unit = models.CharField(max_length=100, blank=True, null=True, verbose_name="Unit #")
    city = models.CharField(max_length=100, blank=True, null=True)
    state = USStateField(blank=True, null=True)
    zip_code = USZipCodeField(blank=True, null=True, verbose_name="ZIP")
    country = models.CharField(max_length=100, blank=True, null=True, default="U.S.A.")

    class Meta:
        abstract = True

    def __unicode__(self):
        return self.name
