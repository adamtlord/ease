from django.db import models


class RidesInProgressManager(models.Manager):
    def get_queryset(self):
        return super(RidesInProgressManager, self).get_queryset().filter(end_date__isnull=True)
