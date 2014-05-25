from django.conf.urls import *
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static

admin.autodiscover()

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browseable API.
urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^api/', include('tigaserver_app.urls')),
    url(r'^webmap/', include('tigamap.urls')),
    url(r'^help/', include('tigahelp.urls')),
) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT)