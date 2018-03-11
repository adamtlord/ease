from django.contrib import admin

from billing.models import Plan, StripeCustomer, Invoice, GroupMembership, Balance, Gift, Subscription


class SubscriptionAdmin(admin.ModelAdmin):
    readonly_fields = ('date_created',)


class GroupMembershipAdmin(admin.ModelAdmin):
    raw_id_fields = ("address", "user", "ride_account", "subscription_account")


admin.site.register(Plan)
admin.site.register(StripeCustomer)
admin.site.register(Invoice)
admin.site.register(GroupMembership, GroupMembershipAdmin)
admin.site.register(Balance)
admin.site.register(Gift)
admin.site.register(Subscription, SubscriptionAdmin)
