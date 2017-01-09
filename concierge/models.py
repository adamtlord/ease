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
    INTRO = 'INTRO'
    PHONE = 'PHONE'
    BILLING = 'BILLING'
    OTHER = 'OTHER'

    TYPE_CHOICES = (
        (INTRO, 'Intro Call'),
        (PHONE, 'Phone Call'),
        (EMAIL, 'Email'),
        (MAIL, 'Mail'),
        (OTHER, 'Other'),
    )

    class Meta:
        ordering = ['-date']

    @property
    def start_date(self):
        return self.date

    def save(self, *args, **kwargs):
        if not self.date:
            self.date = timezone.now()
        if self.type == self.INTRO:
            if self.notes == '':
                self.notes = 'Intro call'
            self.customer.intro_call = True
            self.customer.save()
        return super(Touch, self).save(*args, **kwargs)

    def __unicode__(self):
        return '{} with {} {}'.format(self.type, self.customer.full_name, formats.date_format(self.date, "SHORT_DATETIME_FORMAT"))

    class Meta:
        verbose_name = "Touch"
        verbose_name_plural = "Touches"
