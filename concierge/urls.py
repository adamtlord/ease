from django.contrib.auth import views as auth_views
from django.conf.urls import url

from concierge.views import dashboard, customer_list, customer_create, customer_detail, customer_update, customer_delete

urlpatterns = [
    url(r'^$', dashboard, name='dashboard'),
    url(r'^login/$', auth_views.login, {'template_name': 'concierge/login.html'}, name='concierge_login'),
    url(r'^customers/$', customer_list, name='customer_list'),
    url(r'^customers/create/$', customer_create, name='customer_create'),
    url(r'^customers/(?P<pk>\d+)/$', customer_detail, name='customer_detail'),
    url(r'^customers/(?P<pk>\d+)/update/$', customer_update, name='customer_update'),
    url(r'^customers/(?P<pk>\d+)/delete/$', customer_delete, name='customer_delete'),
]
