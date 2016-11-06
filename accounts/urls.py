from django.conf.urls import url
from accounts.views import customer_list, customer_detail, customer_update, \
    customer_create, customer_delete

urlpatterns = [
    url(r'^$', customer_list, name='customer_list'),
    url(r'^create/$', customer_create, name='customer_create'),
    url(r'^(?P<pk>\d+)/$', customer_detail, name='customer_detail'),
    url(r'^(?P<pk>\d+)/update/$', customer_update, name='customer_update'),
    url(r'^(?P<pk>\d+)/delete/$', customer_delete, name='customer_delete'),
]
