from django.conf.urls import url, include
from accounts.views import (register_self,
                            register_self_payment,
                            register_self_preferences,
                            register_self_destinations,
                            register_self_complete,
                            register_lovedone,
                            register_lovedone_payment,
                            register_lovedone_preferences,
                            register_lovedone_destinations,
                            register_lovedone_complete,
                            register_payment_ride_account,
                            profile,
                            profile_edit,
                            destination_edit,
                            destination_add,
                            destination_delete)

urlpatterns = [
    url(r'^register/$', register_self, name='register_self'),
    url(r'^register/payment/$', register_self_payment, name='register_self_payment'),
    url(r'^register/preferences/$', register_self_preferences, name='register_self_preferences'),
    url(r'^register/destinations/$', register_self_destinations, name='register_self_destinations'),
    url(r'^register/complete/$', register_self_complete, name='register_self_complete'),

    url(r'^register-lovedone/$', register_lovedone, name='register_lovedone'),
    url(r'^register-lovedone/payment/$', register_lovedone_payment, name='register_lovedone_payment'),
    url(r'^register-lovedone/preferences/$', register_lovedone_preferences, name='register_lovedone_preferences'),
    url(r'^register-lovedone/destinations/$', register_lovedone_destinations, name='register_lovedone_destinations'),
    url(r'^register-lovedone/complete/$', register_lovedone_complete, name='register_lovedone_complete'),

    url(r'^register/payment/rides/$', register_payment_ride_account, name='register_payment_ride_account'),

    url(r'^profile/$', profile, name='profile'),
    url(r'^profile/edit/$', profile_edit, name='profile_edit'),

    url(r'^destinations/(?P<destination_id>\d+)/edit/$', destination_edit, name='destination_edit'),
    url(r'^destinations/(?P<destination_id>\d+)/delete/$', destination_delete, name='destination_delete'),
    url(r'^destinations/add/$', destination_add, name='destination_add'),

    url(r'^', include('registration.backends.simple.urls')),
]
