from django.contrib import admin

from billing.models import Plan, StripeCustomer, Invoice


admin.site.register(Plan)
admin.site.register(StripeCustomer)
admin.site.register(Invoice)
