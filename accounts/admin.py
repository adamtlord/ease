from django.contrib import admin

from accounts.models import CustomerProfile, LovedOne
from rides.models import Destination


class DestinationInline(admin.StackedInline):
    model = Destination


class CustomerProfileAdmin(admin.ModelAdmin):
    inlines = [
        DestinationInline
    ]


class LovedOneAdmin(admin.ModelAdmin):
    pass


admin.site.register(CustomerProfile, CustomerProfileAdmin)
admin.site.register(LovedOne, LovedOneAdmin)
