from django.conf.urls import url

from rides.views import (ride_end, ride_edit, ride_delete, ride_detail,
                         ride_detail_modal)

urlpatterns = [
    url(r'^(?P<ride_id>\d+)/$', ride_detail, name='ride_detail'),
    url(r'^(?P<ride_id>\d+)/edit/$', ride_edit, name='ride_edit'),
    url(r'^(?P<ride_id>\d+)/end/$', ride_end, name='ride_end'),
    url(r'^(?P<ride_id>\d+)/delete/$', ride_delete, name='ride_delete'),

    url(r'^(?P<ride_id>\d+)/detail-modal/$', ride_detail_modal, name='ride_detail_modal'),
]
