from django.conf.urls import url, include
from django.contrib.auth import views as auth_views
from accounts.views import (register_self,
                            register_add_funds,
                            register_self_payment,
                            register_self_destinations,
                            register_self_complete,
                            register_lovedone,
                            register_lovedone_payment,
                            register_lovedone_destinations,
                            register_lovedone_complete,
                            register_payment_ride_account,
                            register_payment_redirect,
                            gift_login,
                            gift_purchase,
                            password_validate,
                            profile,
                            profile_edit,
                            profile_add_funds,
                            destination_edit,
                            destination_add,
                            destination_delete)

urlpatterns = [
    url(r'^register/$', register_self, name='register_self'),
    url(r'^register/add-funds/$', register_add_funds, name='register_add_funds'),
    url(r'^register/payment/$', register_self_payment, name='register_self_payment'),
    # url(r'^register/preferences/$', register_self_preferences, name='register_self_preferences'),
    url(r'^register/destinations/$', register_self_destinations, name='register_self_destinations'),
    url(r'^register/complete/$', register_self_complete, name='register_self_complete'),

    url(r'^register-lovedone/$', register_lovedone, name='register_lovedone'),
    url(r'^register-lovedone/payment/$', register_lovedone_payment, name='register_lovedone_payment'),
    # url(r'^register-lovedone/preferences/$', register_lovedone_preferences, name='register_lovedone_preferences'),
    url(r'^register-lovedone/destinations/$', register_lovedone_destinations, name='register_lovedone_destinations'),
    url(r'^register-lovedone/complete/$', register_lovedone_complete, name='register_lovedone_complete'),

    url(r'^register-lovedone/gift/$', register_lovedone, {'gift': True}, name='register_lovedone_gift'),
    url(r'^register-lovedone/gift/payment/$', register_lovedone_payment, {'gift': True}, name='register_lovedone_gift_payment'),

    url(r'^register/payment/rides/$', register_payment_ride_account, name='register_payment_ride_account'),

    url(r'^register/payment/redirect/$', register_payment_redirect, name='register_payment_redirect'),

    url(r'^profile/$', profile, name='profile'),
    url(r'^profile/edit/$', profile_edit, name='profile_edit'),
    url(r'^profile/add-funds/$', profile_add_funds, name='profile_add_funds'),


    url(r'^destinations/(?P<destination_id>\d+)/edit/$', destination_edit, name='destination_edit'),
    url(r'^destinations/(?P<destination_id>\d+)/delete/$', destination_delete, name='destination_delete'),
    url(r'^destinations/add/$', destination_add, name='destination_add'),

    url(r'^gift-login/$', gift_login, name='gift_login'),
    url(r'^gift/(?P<customer_id>\d+)/purchase/$', gift_purchase, name='gift_purchase'),

    url(r'^password_validate/$', password_validate, name='password_validate'),
    url(r'^password/reset/$',
        auth_views.password_reset,
        {
            'html_email_template_name': 'registration/password_reset_html_email.html',
            'email_template_name': 'registration/password_reset_email.txt'
        },
        name='auth_password_reset'
        ),
    url(r'^', include('registration.backends.simple.urls')),
    url('^', include('django.contrib.auth.urls')),
]
