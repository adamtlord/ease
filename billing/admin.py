from django.contrib import admin

from billing.models import Plan, StripeCustomer, Invoice, GroupMembership, Balance, Gift, Subscription


admin.site.register(Plan)
admin.site.register(StripeCustomer)
admin.site.register(Invoice)
admin.site.register(GroupMembership)
admin.site.register(Balance)
admin.site.register(Gift)
admin.site.register(Subscription)
