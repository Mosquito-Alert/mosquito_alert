from django.conf.urls import *
from django.conf.urls.i18n import i18n_patterns
from django.views.generic.base import RedirectView
from django.core.urlresolvers import reverse
from django.contrib.gis import admin
from django.conf import settings
from django.conf.urls.static import static
from tigahelp.views import show_help, show_about, show_license, show_policies, show_terms, show_privacy, \
    show_credit_image
from tigamap import views
from stats.views import show_usage, show_report_users, show_fix_users
from tigaserver_app.views import lookup_photo
from tigacrafting.views import show_validated_photos, show_processing, annotate_tasks, movelab_annotation, movelab_annotation_pending, expert_report_annotation

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
    (r'^i18n/', include('django.conf.urls.i18n')),
    url(r'^webmap/embedded/ca/$', RedirectView.as_view(url='/ca/webmap/embedded/', permanent=False)),
    url(r'^webmap/embedded/es/$', RedirectView.as_view(url='/es/webmap/embedded/', permanent=False)),
    url(r'^webmap/embedded/en/$', RedirectView.as_view(url='/en/webmap/embedded/', permanent=False)),
    url(r'^webmap/ca/$', RedirectView.as_view(url='/ca/webmap/', permanent=False)),
    url(r'^webmap/es/$', RedirectView.as_view(url='/es/webmap/', permanent=False)),
    url(r'^webmap/en/$', RedirectView.as_view(url='/en/webmap/', permanent=False)),
    url(r'^policies/es/$', RedirectView.as_view(url='/es/policies/', permanent=False)),
    url(r'^policies/ca/$', RedirectView.as_view(url='/ca/policies/', permanent=False)),
    url(r'^policies/en/$', RedirectView.as_view(url='/en/policies/', permanent=False)),
    url(r'^terms/es/$', RedirectView.as_view(url='/es/terms/', permanent=False)),
    url(r'^terms/ca/$', RedirectView.as_view(url='/ca/terms/', permanent=False)),
    url(r'^terms/en/$', RedirectView.as_view(url='/en/terms/', permanent=False)),
    url(r'^privacy/es/$', RedirectView.as_view(url='/es/privacy/', permanent=False)),
    url(r'^privacy/ca/$', RedirectView.as_view(url='/ca/privacy/', permanent=False)),
    url(r'^privacy/en/$', RedirectView.as_view(url='/en/privacy/', permanent=False)),
    url(r'^get_photo/(?P<token>\w+)/(?P<photo_uuid>[\w{}.-]{36})/(?P<size>\w+)$', lookup_photo),
) + static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL,
                                                                             document_root=settings.MEDIA_ROOT)

urlpatterns += i18n_patterns('',
    url(r'^policies/$', show_policies, name='help.show_policies'),
    url(r'^terms/$', show_terms, name='help.show_terms'),
    url(r'^privacy/$', show_privacy, name='help.show_privacy'),
    url(r'^webmap/embedded/$', views.show_embedded_adult_map, {'legend': 'legend'}),
    url(r'^webmap/adults/$', views.show_adult_map, name='adult_map'),
    url(r'^webmap/adults/(?P<type>\w+)/$', views.show_adult_map, name='adult_map_type'),
    url(r'^webmap/sites/$', views.show_site_map, name='site_map'),
    url(r'^webmap/sites/(?P<type>\w+)/$', views.show_site_map, name='site_map_type'),
    url(r'^webmap/coverage/$', views.show_new_coverage_map, name='coverage_map'),
    url(r'^webmap/$', views.show_adult_map, name='webmap.show_map_defaults'),
    url(r'^$', views.show_filterable_report_map),
    url(r'^bcn/$', {'limit': 'bcn'}, views.show_filterable_report_map)
    url(r'^single_report_map/(?P<version_uuid>[-\w]+)/$', views.show_single_report_map, name='webmap.single_report'),
    url(r'^photomap/$', views.show_validated_photo_map, name='validated_photo_map'),
    url(r'^stats/$', show_usage),
    url(r'^reportstats/$', show_report_users),
    url(r'^tigacrafting_photos/(?P<type>[-\w]+)/$', show_validated_photos),
    url(r'^expert_validation/$', annotate_tasks, {'how_many': '50', 'which':
    'new'}, name='annotate_tasks_fifty_new'),
    url(r'^expert_validation/(?P<which>\w+)/$', annotate_tasks, name='annotate_tasks'),
    url(r'^expert_validation/(?P<which>\w+)/(?P<scroll_position>\w+)/$', annotate_tasks, name='annotate_tasks_scroll_position'),
    url(r'^movelab_annotation/$', movelab_annotation, name='movelab_annotation'),
    url(r'^movelab_annotation/(?P<tasks_per_page>[0-9]+)/$', movelab_annotation, name='movelab_annotation_tasks_per_page'),
    url(r'^movelab_annotation/(?P<tasks_per_page>[0-9]+)/(?P<scroll_position>\w+)/$', movelab_annotation, name='movelab_annotation_scroll_position'),
    url(r'^movelab_annotation_pending/$', movelab_annotation_pending, name='movelab_annotation_pending'),
    url(r'^movelab_annotation_pending/(?P<tasks_per_page>[0-9]+)/$', movelab_annotation_pending,name='movelab_annotation_pending_tasks_per_page'),
    url(r'^movelab_annotation_pending/(?P<tasks_per_page>[0-9]+)/(?P<scroll_position>\w+)/$', movelab_annotation_pending,name='movelab_annotation_pending_scroll_position'),
    url(r'^experts/$', expert_report_annotation, name='expert_report_annotation'),
    url(r'^experts/(?P<tasks_per_page>[0-9]+)/$', expert_report_annotation, name='expert_report_annotation_tasks_per_page'),
    url(r'^experts/(?P<tasks_per_page>[0-9]+)/(?P<scroll_position>\w+)/$', expert_report_annotation, name='expert_report_annotation_scroll_position'),
    url(r'^coveragestats/$', show_fix_users),
    url(r'^accounts/login/$', 'django.contrib.auth.views.login'),
    url(r'^processing/$', show_processing),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/'}, name='auth_logout'),
)
