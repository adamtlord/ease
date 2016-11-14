from django.conf.urls import url, include
from accounts.views import register_self, register_self_preferences, register_self_destinations, register_lovedone, profile

urlpatterns = [
    url(r'^register/$', register_self, name='register_self'),
    url(r'^register/preferences/$', register_self_preferences, name='register_self_preferences'),
    url(r'^register/destinations/$', register_self_destinations, name='register_self_destinations'),
    url(r'^register-lovedone/$', register_lovedone, name='register_lovedone'),
    url(r'^profile/$', profile, name='profile'),
    url(r'^', include('registration.backends.simple.urls')),
]
