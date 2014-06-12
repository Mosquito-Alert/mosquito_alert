from django.conf.urls import *
from django.conf.urls.i18n import i18n_patterns
from django.views.generic.base import RedirectView
from django.core.urlresolvers import reverse
from django.contrib import admin
from django.conf import settings
from django.conf.urls.static import static
from tigahelp.views import show_help, show_about, show_license, show_policies, show_terms, show_privacy, \
    show_credit_image
from tigamap import views

admin.autodiscover()

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browseable API.
urlpatterns = patterns('',
    url(r'^admin/', include(admin.site.urls)),
    url(r'^api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    url(r'^api/', include('tigaserver_app.urls')),
    url(r'^webapp/', include('webapp.urls')),
    url(r'^help/(?P<platform>\w+)/(?P<language>\w+)/$', show_help),
    url(r'^about/(?P<platform>\w+)/(?P<language>\w+)/$', show_about),
    url(r'^credits/$', show_credit_image, name='show_credit_image'),
    url(r'^license/(?P<platform>\w+)/(?P<language>\w+)/$', show_license),
    url(r'^policies/(?P<language>\w+)/$', show_policies),
    url(r'^terms/(?P<language>\w+)/$', show_terms),
    url(r'^privacy/(?P<language>\w+)/$', show_privacy),
    (r'^i18n/', include('django.conf.urls.i18n')),
) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL,
                                                                             document_root=settings.MEDIA_ROOT)

urlpatterns += i18n_patterns('',
    url(r'^webmap/embedded/(?P<language>\w+)/$', views.show_embedded_webmap, name='webmap.show_embedded_webmap'),
    url(r'^webmap/embedded/$', views.show_embedded_webmap),
    url(r'^webmap/(?P<report_type>\w+)/(?P<category>\w+)/(?P<data>\w+)/$', views.show_map, name='webmap'
                                                                                                '.show_map_beta'),
    url(r'^webmap/(?P<report_type>\w+)/(?P<category>\w+)/$', views.show_map, name='webmap.show_map'),
    url(r'^webmap/(?P<report_type>\w+)/$', views.show_map),
    url(r'^webmap/$', views.show_map),
    url(r'^webmap/testingzone/(?P<report_type>\w+)/(?P<category>\w+)/$', views.show_map),
    url(r'^webmap/testingzone/(?P<report_type>\w+)/$', views.show_map),
    url(r'^webmap/testingzone/$', views.show_map),
)
