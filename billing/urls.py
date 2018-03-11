from django.conf.urls import url
from billing.views import (customer_subscription_account_edit,
                           customer_ride_account_edit, rides_ready_to_bill,
                           rides_incomplete, rides_upload, rides_invoiced, retrieve_coupon,
                           group_billing)

urlpatterns = [
    url(r'^subscription-account/$', customer_subscription_account_edit, name='customer_subscription_account_edit'),
    url(r'^ride-account/$', customer_ride_account_edit, name='customer_ride_account_edit'),

    url(r'^group-subscription-account/$', customer_subscription_account_edit, {'group_as_customer': True}, name='group_subscription_account_edit'),
    url(r'^group-ride-account/$', customer_ride_account_edit, {'group_as_customer': True}, name='group_ride_account_edit'),

    url(r'^ready-to-bill/$', rides_ready_to_bill, name='rides_ready_to_bill'),
    url(r'^incomplete/$', rides_incomplete, name='rides_incomplete'),
    url(r'^invoiced/$', rides_invoiced, name='rides_invoiced'),
    url(r'^upload/$', rides_upload, name='rides_upload'),
    url(r'^group-billing/$', group_billing, name='group_billing'),

    # AJAX
    url(r'^retrieve_coupon/$', retrieve_coupon, name='retrieve_coupon'),
]
