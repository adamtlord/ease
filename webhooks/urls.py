from django.conf.urls import url
from webhooks.views import invoice, charge_failed

urlpatterns = [
    url(r'^invoice/$', invoice, name='invoice'),
    url(r'^charge-failed/$', charge_failed, name='charge_failed')
]
