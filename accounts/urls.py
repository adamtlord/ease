from django.conf.urls import url, include
from accounts.views import (register_self, register_self_preferences,
                            register_self_destinations,
                            register_self_complete,
                            register_lovedone, profile,
                            register_lovedone_preferences,
                            register_lovedone_destinations,
                            register_lovedone_complete,
                            profile_edit,
                            destinations_edit)

urlpatterns = [
    url(r'^register/$', register_self, name='register_self'),
    url(r'^register/preferences/$', register_self_preferences, name='register_self_preferences'),
    url(r'^register/destinations/$', register_self_destinations, name='register_self_destinations'),
    url(r'^register/complete/$', register_self_complete, name='register_self_complete'),
    url(r'^register-lovedone/$', register_lovedone, name='register_lovedone'),
    url(r'^register-lovedone/preferences/$', register_lovedone_preferences, name='register_lovedone_preferences'),
    url(r'^register-lovedone/destinations/$', register_lovedone_destinations, name='register_lovedone_destinations'),
    url(r'^register-lovedone/complete/$', register_lovedone_complete, name='register_lovedone_complete'),
    url(r'^profile/$', profile, name='profile'),
    url(r'^profile/edit/$', profile_edit, name='profile_edit'),
    url(r'^destinations/edit/$', destinations_edit, name='destinations_edit'),
    url(r'^', include('registration.backends.simple.urls')),
]
