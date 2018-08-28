from django.db import models
from django.db.models import Q
from django.utils import timezone


class RidesInProgressManager(models.Manager):
    def get_queryset(self):
        return super(RidesInProgressManager, self).get_queryset().filter(end_date__isnull=True)


class RidesReadyToBillManager(models.Manager):
    def get_queryset(self):
        return super(RidesReadyToBillManager, self).get_queryset() \
            .filter(complete=True) \
            .exclude(invoiced=True) \
            .exclude(cost__isnull=True) \
            .exclude(invoice_id__isnull=False) \
            .exclude(cancelled=True) \
            .prefetch_related('customer')


class RidesIncompleteManager(models.Manager):
    def get_queryset(self):
        return super(RidesIncompleteManager, self).get_queryset() \
            .filter(Q(cost__isnull=True) | Q(complete=False) | Q(distance__isnull=True))


class ActiveRidesManager(models.Manager):
    def get_queryset(self):
        return super(ActiveRidesManager, self).get_queryset() \
            .filter(start_date__lte=timezone.now()) \
            .exclude(complete=True) \
            .exclude(cancelled=True) \
            .prefetch_related('customer')
