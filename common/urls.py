from django.conf.urls import url, include
from common import views

urlpatterns = [
    url(r'^$', views.homepage, name='homepage'),
    url(r'^accounts/', include('registration.backends.hmac.urls'))
]
