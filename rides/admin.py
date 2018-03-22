from django.contrib import admin

from rides.models import Destination, Ride, RideConfirmation


admin.site.register(Destination)
admin.site.register(Ride)
admin.site.register(RideConfirmation)
