from django.contrib import admin

from rides.models import Destination, Ride, RideConfirmation


class RideAdmin(admin.ModelAdmin):
    raw_id_fields = ("destination", "start", "customer", "rider_link")


admin.site.register(Destination)
admin.site.register(Ride, RideAdmin)
admin.site.register(RideConfirmation)
