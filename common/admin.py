from django.contrib import admin

from common.models import Location


class LocationAdmin(admin.ModelAdmin):
    pass

admin.site.register(Location, LocationAdmin)
