from django.conf.urls import *
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from tigahelp.views import show_help, show_about, show_license, show_policies, show_terms_en, show_privacy_en

admin.autodiscover()

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browseable API.
urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^api/', include('tigaserver_app.urls')),
    url(r'^webmap/', include('tigamap.urls')),
    url(r'^webapp/', include('webapp.urls')),
    url(r'^help/(?P<platform>\w+)/(?P<language>\w+)/$', show_help),
    url(r'^about/(?P<platform>\w+)/(?P<language>\w+)/$', show_about),
    url(r'^license/(?P<platform>\w+)/(?P<language>\w+)/$', show_license),
    url(r'^policies/(?P<language>\w+)/$', show_policies),
    url(r'^terms/(?P<language>\w+)/$', show_policies),
    url(r'^privacy/(?P<language>\w+)/$', show_policies),
    url(r'^testingzone/privacy/$', show_privacy_en, name='show_privacy_en'),
    url(r'^testingzone/terms/$', show_terms_en, name='show_terms_en'),
) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL,
                                                                             document_root=settings.MEDIA_ROOT)