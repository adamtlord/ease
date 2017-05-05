from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.views.defaults import page_not_found, server_error

from rest_framework import routers

from accounts.viewsets import UserViewSet, CustomerViewSet
from rides.viewsets import RideViewSet, DestinationViewSet
from billing.viewsets import PlanViewSet, GroupMembershipViewSet

from django.contrib import admin
admin.autodiscover()

router = routers.DefaultRouter()
router.register(r'customers', CustomerViewSet)
router.register(r'users', UserViewSet)
router.register(r'rides', RideViewSet)
router.register(r'destinations', DestinationViewSet)
router.register(r'plans', PlanViewSet)
router.register(r'group-memberships', GroupMembershipViewSet)


urlpatterns = [
    url(r'^$', auth_views.login, {'template_name': 'registration/login.html'}, name='homepage'),
    url(r'', include('accounts.urls')),
    url(r'^concierge/billing/', include('billing.urls')),
    url(r'^concierge/ride/', include('rides.urls')),
    url(r'^concierge/', include('concierge.urls')),
    url(r'^webhooks/', include('webhooks.urls')),
    url(r'^admin/', include(admin.site.urls)),

    url(r'^api/', include(router.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework'))
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += [
        url(r'^404/$', page_not_found),
        url(r'^500/$', server_error),
    ]
