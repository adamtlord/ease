from django.contrib import admin

from billing.models import Plan, StripeCustomer, Invoice, GroupMembership, Balance, Gift, Subscription


class SubscriptionAdmin(admin.ModelAdmin):
    readonly_fields = ('date_created',)


class GroupMembershipAdmin(admin.ModelAdmin):
    raw_id_fields = ("address", "user", "ride_account", "subscription_account")


class StripeCustomerAdmin(admin.ModelAdmin):
    list_display = ["first_name", "last_name", "customer"]
    search_fields = ["first_name", "last_name", "customer__first_name", "customer__last_name"]
    raw_id_fields = ["customer"]


admin.site.register(Plan)
admin.site.register(StripeCustomer, StripeCustomerAdmin)
admin.site.register(Invoice)
admin.site.register(GroupMembership, GroupMembershipAdmin)
admin.site.register(Balance)
admin.site.register(Gift)
admin.site.register(Subscription, SubscriptionAdmin)
