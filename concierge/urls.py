from django.contrib.auth import views as auth_views
from django.conf.urls import url

from concierge.views import (dashboard, upcoming_rides, rides_history, customer_list,
                             customer_list_inactive, customer_create, customer_detail,
                             customer_update, customer_delete, customer_search_data,
                             customer_destinations, customer_destination_edit,
                             customer_destination_add, customer_destination_delete,
                             payment_subscription_account_edit,
                             payment_ride_account_edit,
                             customer_history,
                             customer_activity_add,
                             )

from rides.views import (ride_start, customer_rides)


urlpatterns = [
    url(r'^$', dashboard, name='dashboard'),
    url(r'^login/$', auth_views.login, {'template_name': 'concierge/login.html'}, name='concierge_login'),
    url(r'^upcoming-rides/$', upcoming_rides, name='upcoming_rides'),
    url(r'^rides-histry/$', rides_history, name='rides_history'),
    url(r'^customers/$', customer_list, name='customer_list'),
    url(r'^customers-inactive/$', customer_list_inactive, name='customer_list_inactive'),
    url(r'^customers/create/$', customer_create, name='customer_create'),
    url(r'^customers/(?P<customer_id>\d+)/$', customer_detail, name='customer_detail'),
    url(r'^customers/(?P<customer_id>\d+)/update/$', customer_update, name='customer_update'),
    url(r'^customers/(?P<customer_id>\d+)/delete/$', customer_delete, name='customer_delete'),

    url(r'^customers/(?P<customer_id>\d+)/destinations/$', customer_destinations, name='customer_destinations'),
    url(r'^customers/(?P<customer_id>\d+)/destination/add/$', customer_destination_add, name='customer_destination_add'),
    url(r'^customers/(?P<customer_id>\d+)/destination/(?P<destination_id>\d+)/edit/$', customer_destination_edit, name='customer_destination_edit'),
    url(r'^customers/(?P<customer_id>\d+)/destination/(?P<destination_id>\d+)/delete/$', customer_destination_delete, name='customer_destination_delete'),

    url(r'^customers/(?P<customer_id>\d+)/rides/$', customer_rides, name='customer_rides'),
    url(r'^customers/(?P<customer_id>\d+)/ride/start/$', ride_start, name='ride_start'),

    url(r'^customers/(?P<customer_id>\d+)/history/$', customer_history, name='customer_history'),
    url(r'^customers/(?P<customer_id>\d+)/activity/add/$', customer_activity_add, name='customer_activity_add'),

    url(r'^customers/(?P<customer_id>\d+)/payment/subscription/$', payment_subscription_account_edit, name='payment_subscription_account_edit'),
    url(r'^customers/(?P<customer_id>\d+)/payment/ride/$', payment_ride_account_edit, name='payment_ride_account_edit'),



    # AJAX
    url(r'^customers/search/$', customer_search_data, name='customer_search_data'),
]
