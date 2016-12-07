from __future__ import unicode_literals

from django.db import models


class Touch(models.Model):
    customer = models.ForeignKey('accounts.Customer')
    date = models.DateTimeField(blank=True, null=True)
    type = models.CharField(max_length=255, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    @property
    def start_date(self):
        return self.date
