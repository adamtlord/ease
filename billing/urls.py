from django.conf.urls import url, include
from billing.views import (customer_subscription_account_edit,
                           customer_ride_account_edit)

urlpatterns = [
    url(r'^subscription_account/$', customer_subscription_account_edit, name='customer_subscription_account_edit'),
    url(r'^ride_account/$', customer_ride_account_edit, name='customer_ride_account_edit'),
]
