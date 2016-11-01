from __future__ import unicode_literals

from django.db import models
from common.models import Location


class Destination(Location):
    name = models.CharField(max_length=50)
    nickname = models.CharField(max_length=50, blank=True, null=True)
