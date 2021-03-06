from django.contrib.auth import views as auth_views
from django.conf.urls import url

from concierge.views import (dashboard, upcoming_rides, active_rides, rides_history,
                             customer_list, customer_list_inactive, customer_create,
                             customer_upload,
                             customer_detail, customer_update,
                             customer_search_data, customer_destinations,
                             customer_destination_edit, customer_destination_add,
                             customer_destination_delete,
                             payment_subscription_account_edit,
                             payment_ride_account_edit,
                             customer_history,
                             customer_activity_add,
                             customer_deactivate,
                             customer_activate,
                             concierge_settings,
                             customer_data_export,
                             customer_add_funds,
                             group_membership_list,
                             group_membership_detail,
                             group_membership_add_customer,
                             group_membership_edit,
                             gift_credit_report,
                             ggg_customer_export,
                             ggg_group_export
                             )

from rides.views import (ride_start, customer_rides)


urlpatterns = [
    url(r'^$', dashboard, name='dashboard'),
    url(r'^login/$', auth_views.login, {'template_name': 'concierge/login.html'}, name='concierge_login'),
    url(r'^settings/$', concierge_settings, name='concierge_settings'),
    url(r'^upcoming-rides/$', upcoming_rides, name='upcoming_rides'),
    url(r'^active-rides/$', active_rides, name='active_rides'),
    url(r'^rides-history/$', rides_history, name='rides_history'),
    url(r'^customers/$', customer_list, name='customer_list'),
    url(r'^customers-inactive/$', customer_list_inactive, name='customer_list_inactive'),
    url(r'^customers/create/$', customer_create, name='customer_create'),
    url(r'^customers/upload/$', customer_upload, name='customer_upload'),
    url(r'^customers/(?P<customer_id>\d+)/$', customer_detail, name='customer_detail'),
    url(r'^customers/(?P<customer_id>\d+)/update/$', customer_update, name='customer_update'),

    url(r'^customers/(?P<customer_id>\d+)/deactivate/$', customer_deactivate, name='customer_deactivate'),
    url(r'^customers/(?P<customer_id>\d+)/activate/$', customer_activate, name='customer_activate'),

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

    url(r'^customers/(?P<customer_id>\d+)/add-funds/$', customer_add_funds, name='customer_add_funds'),

    url(r'^group-memberships/$', group_membership_list, name='group_membership_list'),
    url(r'^group-memberships/(?P<group_id>\d+)/$', group_membership_detail, name='group_membership_detail'),
    url(r'^group-memberships/(?P<group_id>\d+)/edit/$', group_membership_edit, name='group_membership_edit'),
    url(r'^group-memberships/(?P<customer_id>\d+)/payment/subscription/$', payment_subscription_account_edit, {'group_as_customer': True}, name='group_payment_subscription_account_edit'),
    url(r'^group-memberships/(?P<customer_id>\d+)/payment/ride/$', payment_ride_account_edit, {'group_as_customer': True}, name='group_payment_ride_account_edit'),
    url(r'^group-memberships/(?P<group_id>\d+)/add-customer/$', group_membership_add_customer, name='group_membership_add_customer'),

    # AJAX
    url(r'^customers/search/$', customer_search_data, name='customer_search_data'),
    url(r'^customers/export/$', customer_data_export, name='customer_data_export'),

    url(r'^customers/export/intentionally-obfuscated-url/$', ggg_customer_export, name='ggg_customer_export'),
    url(r'^customers/export/groups/intentionally-obfuscated-url/$', ggg_group_export, name='ggg_group_export'),

    url(r'^gift-credit-report/$', gift_credit_report, name='gift_credit_report'),
]
