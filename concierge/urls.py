from django.contrib.auth import views as auth_views
from django.conf.urls import url

from concierge.views import (dashboard, customer_list, customer_create,
                             customer_detail, customer_update,
                             customer_delete, customer_search_data,
                             customer_destinations, destination_edit,
                             destination_add, destination_delete,
                             payment_subscription_account_edit,
                             payment_ride_account_edit,
                             )
from rides.views import (ride_start, ride_end, ride_edit, ride_detail, customer_rides)


urlpatterns = [
    url(r'^$', dashboard, name='dashboard'),
    url(r'^login/$', auth_views.login, {'template_name': 'concierge/login.html'}, name='concierge_login'),
    url(r'^customers/$', customer_list, name='customer_list'),
    url(r'^customers/create/$', customer_create, name='customer_create'),
    url(r'^customers/(?P<customer_id>\d+)/$', customer_detail, name='customer_detail'),
    url(r'^customers/(?P<customer_id>\d+)/update/$', customer_update, name='customer_update'),
    url(r'^customers/(?P<customer_id>\d+)/delete/$', customer_delete, name='customer_delete'),

    url(r'^customers/(?P<customer_id>\d+)/destinations/$', customer_destinations, name='customer_destinations'),
    url(r'^customers/(?P<customer_id>\d+)/destination/add/$', destination_add, name='destination_add'),
    url(r'^customers/(?P<customer_id>\d+)/destination/(?P<destination_id>\d+)/edit/$', destination_edit, name='destination_edit'),
    url(r'^customers/(?P<customer_id>\d+)/destination/(?P<destination_id>\d+)/delete/$', destination_delete, name='destination_delete'),

    url(r'^customers/(?P<customer_id>\d+)/rides/$', customer_rides, name='customer_rides'),
    url(r'^customers/(?P<customer_id>\d+)/ride/start/$', ride_start, name='ride_start'),
    url(r'^customers/(?P<customer_id>\d+)/ride/(?P<ride_id>\d+)/$', ride_detail, name='ride_detail'),
    url(r'^customers/(?P<customer_id>\d+)/ride/(?P<ride_id>\d+)/edit/$', ride_edit, name='ride_edit'),
    url(r'^customers/(?P<customer_id>\d+)/ride/(?P<ride_id>\d+)/end/$', ride_end, name='ride_end'),

    url(r'^customers/(?P<customer_id>\d+)/payment/subscription/$', payment_subscription_account_edit, name='payment_subscription_account_edit'),
    url(r'^customers/(?P<customer_id>\d+)/payment/ride/$', payment_ride_account_edit, name='payment_ride_account_edit'),

    # AJAX
    url(r'^customers/search/$', customer_search_data, name='customer_search_data'),
]
