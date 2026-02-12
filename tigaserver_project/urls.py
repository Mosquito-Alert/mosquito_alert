from django.conf.urls import *
from django.conf.urls.i18n import i18n_patterns
from django.views.generic.base import RedirectView
from django.http import HttpResponsePermanentRedirect
from django.utils.translation import get_language

from django.contrib.gis import admin

from django.conf import settings
from django.conf.urls.static import static
from stats.views import show_usage, workload_stats, \
    stats_user_score, stats_user_ranking, global_assignments, global_assignments_list
from tigacrafting.views import expert_report_annotation, expert_status, picture_validation, notifications_version_two, notification_detail, notifications_table, user_notifications_datatable, entolab_license_agreement, expert_report_pending, expert_report_complete, entolab_license_agreement, report_expiration, aimalog_datatable, aimalog, coarse_filter
from django.views.i18n import JavaScriptCatalog
from django.urls import include,path
from django.contrib.auth import views as auth_views
from django.views.generic import TemplateView

admin.autodiscover()

# Wire up our API using automatic URL routing.
# Additionally, we include login URLs for the browseable API.

urlpatterns = [
    path('api/', include('tigaserver_project.api_urls')),
    path('api/', include(('tigaserver_app.urls', 'tigaserver_app'), namespace='legacy')),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('api-docs/', TemplateView.as_view(template_name='swagger.html',extra_context={'schema_url':'openapi-schema'}), name='swagger-ui'),
]

urlpatterns += [
    path('admin/', admin.site.urls),
    path('i18n/', include('django.conf.urls.i18n')),
]
admin.site.site_header = "Mosquito Alert administration"
admin.site.site_title = "Mosquito Alert"

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += i18n_patterns(
    path(
        'terms/',
        lambda request: HttpResponsePermanentRedirect(
            f"https://app.mosquitoalert.com/{get_language() or 'en'}/legal/terms"
        ),
    ),
    path(
        'privacy/',
        lambda request: HttpResponsePermanentRedirect(
            f"https://app.mosquitoalert.com/{get_language() or 'en'}/legal/privacy"
        ),
    ),
    path(
        'scoring/',
        lambda request: HttpResponsePermanentRedirect(
            f"https://app.mosquitoalert.com/{get_language() or 'en'}/info/score"
        ),
    ),
    path('about_us/', RedirectView.as_view(url='https://www.mosquitoalert.com', permanent=True)),
    path('project_about/', RedirectView.as_view(url='https://www.mosquitoalert.com', permanent=True)),
    path('webmap/embedded/', RedirectView.as_view(url='https://map.mosquitoalert.com', permanent=True)),
    path('webmap/adults/', RedirectView.as_view(url='https://map.mosquitoalert.com', permanent=True)),
    path('webmap/adults/<selected_validation>/', RedirectView.as_view(url='https://map.mosquitoalert.com', permanent=True)),
    path('webmap/sites/', RedirectView.as_view(url='https://map.mosquitoalert.com', permanent=True)),
    path('webmap/sites/<selected_validation>/', RedirectView.as_view(url='https://map.mosquitoalert.com', permanent=True)),
    path('webmap/coverage/', RedirectView.as_view(url='https://map.mosquitoalert.com', permanent=True)),
    path('webmap/', RedirectView.as_view(url='https://map.mosquitoalert.com', permanent=True)),
    path('', RedirectView.as_view(url='https://map.mosquitoalert.com', permanent=True)),
    path('bcn/', RedirectView.as_view(url='https://map.mosquitoalert.com', permanent=True)),
    path('single_report_map/<uuid:version_uuid>/', RedirectView.as_view(url='https://map.mosquitoalert.com/%(version_uuid)s/', permanent=True)),
    path('single_simple/<uuid:version_uuid>/', RedirectView.as_view(url='https://map.mosquitoalert.com/%(version_uuid)s/', permanent=True)),
    path('stats/', show_usage, name='show_usage'),
    path('stats/workload/', workload_stats, name='workload_stats'),
    path('stats/workload/<country_id>/', workload_stats, name='workload_stats'),
    path('stats/global_assignments/', global_assignments, name='global_assignments'),
    path('stats/global_assignments_list/<country_code>/<status>/', global_assignments_list, name='global_assignments_list'),

    path('stats/user_score/<user_uuid>', stats_user_score, name='stats_user_score'),
    path('stats/user_ranking/<page>', stats_user_ranking, name='stats_user_ranking'),
    path('stats/user_ranking/<page>/<user_uuid>', stats_user_ranking, name='stats_user_ranking'),

    path('experts/', expert_report_annotation, name='expert_report_annotation'),
    path('experts/report_expiration/', report_expiration, name='report_expiration'),
    path('experts/report_expiration/<int:country_id>/', report_expiration, name='report_expiration'),
    path('entolab_license_agreement/', entolab_license_agreement, name='entolab_license_agreement'),
    path('experts/status/reports/', RedirectView.as_view(url='https://app.mosquitoalert.com/identification_tasks/', permanent=True), name='expert_report_status'),
    path('experts/status/reports/pending', expert_report_pending, name='expert_report_pending'),
    path('experts/status/reports/complete', expert_report_complete, name='expert_report_complete'),
    path('experts/status/reports/single/<uuid:version_uuid>/', RedirectView.as_view(url='https://app.mosquitoalert.com/identification_tasks/%(version_uuid)s/', permanent=True), name='single_report_view'),
    path('experts/status/people/', expert_status, name='expert_status'),
    path('photo_grid/', picture_validation, name='picture_validation'),
    path('coarse_filter/', coarse_filter, name='coarse_filter'),
    path('notifications/', notifications_version_two, name='notifications'),
    path('notifications/list', notifications_table, name='notifications_table'),
    path('notifications/apilist', user_notifications_datatable, name='user_notifications_datatable'),
    path('notifications/detail/<int:notification_id>', notification_detail, name='notification_detail'),
    path('aimalog/', aimalog, name='aimalog'),
    path('aimalog/apilist/', aimalog_datatable, name='aimalog_datatable'),

    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), {'next_page': '/experts/'}, name='auth_logout'),

    path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),
)
