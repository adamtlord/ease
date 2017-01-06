from django.conf.urls import url

from rides.views import (ride_end, ride_edit, ride_delete, ride_detail, rides_ready_to_bill,
                         rides_incomplete, rides_upload, rides_invoiced
                         )

urlpatterns = [
    url(r'^ride/(?P<ride_id>\d+)/$', ride_detail, name='ride_detail'),
    url(r'^ride/(?P<ride_id>\d+)/edit/$', ride_edit, name='ride_edit'),
    url(r'^ride/(?P<ride_id>\d+)/end/$', ride_end, name='ride_end'),
    url(r'^ride/(?P<ride_id>\d+)/delete/$', ride_delete, name='ride_delete'),

    url(r'^billing/ready-to-bill/$', rides_ready_to_bill, name='rides_ready_to_bill'),
    url(r'^billing/incomplete/$', rides_incomplete, name='rides_incomplete'),
    url(r'^billing/invoiced/$', rides_invoiced, name='rides_invoiced'),
    url(r'^billing/upload/$', rides_upload, name='rides_upload'),
]
