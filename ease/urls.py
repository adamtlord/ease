from django.conf import settings
from django.conf.urls import url, include
from django.conf.urls.static import static
from django.contrib.auth import views as auth_views
from django.views.defaults import page_not_found, server_error

from django.contrib import admin
admin.autodiscover()

urlpatterns = [
    url(r'^$', auth_views.login, {'template_name': 'registration/login.html'}, name='homepage'),
    url(r'', include('accounts.urls')),
    url(r'^concierge/', include('concierge.urls')),
    url(r'^admin/', include(admin.site.urls)),
]

if settings.DEBUG:
    urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)
    urlpatterns += static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

if settings.DEBUG:
    urlpatterns += [
        url(r'^404/$', page_not_found),
        url(r'^500/$', server_error),
    ]
