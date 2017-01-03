from django.db import models
from django.db.models import Q


class RidesInProgressManager(models.Manager):
    def get_queryset(self):
        return super(RidesInProgressManager, self).get_queryset().filter(end_date__isnull=True)


class RidesReadyToBillManager(models.Manager):
    def get_queryset(self):
        return super(RidesReadyToBillManager, self).get_queryset().filter(complete=True).exclude(cost__isnull=True).exclude(invoice_id__isnull=False)


class RidesIncompleteManager(models.Manager):
    def get_queryset(self):
        return super(RidesIncompleteManager, self).get_queryset().filter(Q(cost__isnull=True) | Q(end_date__isnull=True) | Q(distance__isnull=True))
