from django.conf.urls import url
from webhooks.views import invoice

urlpatterns = [
    url(r'^invoice/$', invoice, name='invoice'),
]
