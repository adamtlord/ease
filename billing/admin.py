from django.contrib import admin

from billing.models import Plan, StripeCustomer


admin.site.register(Plan)
admin.site.register(StripeCustomer)
