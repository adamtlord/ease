from django.conf.urls import url
from webhooks.views import (invoice_item,
                            invoice,
                            invoice_paid)

urlpatterns = [
    url(r'^invoice-item/$', invoice_item, name='invoice_item'),

    url(r'^invoice/$', invoice, name='invoice'),
    url(r'^invoice-paid/$', invoice_paid, name='invoice_paid'),
]
