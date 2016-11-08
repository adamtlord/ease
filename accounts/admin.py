from django.contrib import admin

from accounts.models import Customer, LovedOne
from rides.models import Destination


class DestinationInline(admin.StackedInline):
    model = Destination


class CustomerAdmin(admin.ModelAdmin):
    inlines = [
        DestinationInline
    ]


class LovedOneAdmin(admin.ModelAdmin):
    pass


admin.site.register(Customer, CustomerAdmin)
admin.site.register(LovedOne, LovedOneAdmin)
