from __future__ import unicode_literals

from django.db import models
from django.utils import timezone
from django.utils import formats


class Touch(models.Model):
    customer = models.ForeignKey('accounts.Customer')
    date = models.DateTimeField(blank=True, null=True)
    type = models.CharField(max_length=255, null=True, blank=True)
    notes = models.TextField(blank=True, null=True)

    EMAIL = 'EMAIL'
    MAIL = 'MAIL'
    PHONE = 'PHONE'
    OTHER = 'OTHER'

    TYPE_CHOICES = (
        (EMAIL, 'Email'),
        (MAIL, 'Mail'),
        (PHONE, 'Phone Call'),
        (OTHER, 'Other'),
    )

    @property
    def start_date(self):
        return self.date

    def save(self, *args, **kwargs):
        if not self.date:
            self.date = timezone.now()
        return super(Touch, self).save(*args, **kwargs)

    def __unicode__(self):
        return '{} with {} {}'.format(self.type, self.customer.full_name, formats.date_format(self.date, "SHORT_DATETIME_FORMAT"))

    class Meta:
        verbose_name = "Touch"
        verbose_name_plural = "Touches"
