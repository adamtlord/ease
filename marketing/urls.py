from django.conf.urls import url
from marketing.views import homepage

urlpatterns = [
    url(r'^$', homepage, name='homepage'),
]
