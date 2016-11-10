from django.conf.urls import url, include
from registration.backends.simple.views import RegistrationView
from accounts.forms import CustomUserRegistrationForm

urlpatterns = [
    url(r'^register/$', RegistrationView.as_view(form_class=CustomUserRegistrationForm), name='registration_register',),
    url(r'^', include('registration.backends.simple.urls')),
]
