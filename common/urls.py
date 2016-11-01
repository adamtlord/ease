from django.conf.urls import url
from common import views

urlpatterns = [
    url(r'^$', views.homepage, name='homepage'),
]
