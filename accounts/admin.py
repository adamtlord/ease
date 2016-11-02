from django.contrib import admin

from accounts.models import CustomerProfile, LovedOne


class CustomerProfileAdmin(admin.ModelAdmin):
    pass


class LovedOneAdmin(admin.ModelAdmin):
    pass


admin.site.register(CustomerProfile, CustomerProfileAdmin)
admin.site.register(LovedOne, LovedOneAdmin)
