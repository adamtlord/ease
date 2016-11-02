from django.contrib import admin

from rides.models import Destination


class DestinationAdmin(admin.ModelAdmin):
    pass

admin.site.register(Destination, DestinationAdmin)
