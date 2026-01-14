from django.conf.urls import *
from django.conf.urls.i18n import i18n_patterns
from django.views.generic.base import RedirectView
from django.http import HttpResponsePermanentRedirect
from django.utils.translation import get_language

from django.contrib.gis import admin

from django.conf import settings
from django.conf.urls.static import static
from tigahelp.views import show_about_us, show_project_about, show_app_license
from stats.views import show_usage, workload_stats, report_stats, registration_stats, report_stats_ccaa, report_stats_ccaa_pie, \
    report_stats_ccaa_pie_sites, mosquito_ccaa_rich, mosquito_ccaa_rich_iframetest, mosquito_ccaa_rich_iframetest_sites, speedmeter, stats_directory, \
    adult_sunburst, site_sunburst, hashtag_map, stats_user_score, stats_user_ranking, expert_report_assigned_data, global_assignments, global_assignments_list
from tigacrafting.views import expert_report_annotation, expert_report_status, expert_status, picture_validation, notifications_version_two, notification_detail, notifications_table, user_notifications_datatable, single_report_view, entolab_license_agreement, metadataPhoto, expert_report_pending, expert_report_complete, entolab_license_agreement, predefined_messages, expert_geo_report_assign, report_expiration, aimalog_datatable, aimalog, coarse_filter
from tigaserver_messages.views import compose_w_data, reply_w_data, compose
from django_messages.views import view,delete,undelete,trash,inbox,outbox
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
    path('about_us/es/', RedirectView.as_view(url='/es/about_us/', permanent=False), name="about_us_es"),
    path('about_us/ca/', RedirectView.as_view(url='/ca/about_us/', permanent=False), name="about_us_ca"),
    path('about_us/en/', RedirectView.as_view(url='/en/about_us/', permanent=False), name="about_us_en"),
    path('about_us/de/', RedirectView.as_view(url='/de/about_us/', permanent=False), name="about_us_de"),
    path('about_us/sq/', RedirectView.as_view(url='/sq/about_us/', permanent=False), name="about_us_sq"),
    path('about_us/el/', RedirectView.as_view(url='/el/about_us/', permanent=False), name="about_us_el"),
    path('about_us/hu/', RedirectView.as_view(url='/hu/about_us/', permanent=False), name="about_us_hu"),
    path('about_us/pt/', RedirectView.as_view(url='/pt/about_us/', permanent=False), name="about_us_pt"),
    path('about_us/sl/', RedirectView.as_view(url='/sl/about_us/', permanent=False), name="about_us_sl"),
    path('about_us/bg/', RedirectView.as_view(url='/bg/about_us/', permanent=False), name="about_us_bg"),
    path('about_us/ro/', RedirectView.as_view(url='/ro/about_us/', permanent=False), name="about_us_ro"),
    path('about_us/hr/', RedirectView.as_view(url='/hr/about_us/', permanent=False), name="about_us_hr"),
    path('about_us/mk/', RedirectView.as_view(url='/mk/about_us/', permanent=False), name="about_us_mk"),
    path('about_us/sr/', RedirectView.as_view(url='/sr/about_us/', permanent=False), name="about_us_sr"),
    path('about_us/lb/', RedirectView.as_view(url='/lb/about_us/', permanent=False), name="about_us_lb"),
    path('about_us/nl/', RedirectView.as_view(url='/nl/about_us/', permanent=False), name="about_us_nl"),
    path('about_us/tr/', RedirectView.as_view(url='/tr/about_us/', permanent=False), name="about_us_tr"),
    path('about_us/bn/', RedirectView.as_view(url='/bn/about_us/', permanent=False), name="about_us_bn"),
    path('about_us/sv/', RedirectView.as_view(url='/sv/about_us/', permanent=False), name="about_us_sv"),
    path('project_about/es/', RedirectView.as_view(url='/es/project_about/', permanent=False), name="project_about_es"),
    path('project_about/ca/', RedirectView.as_view(url='/ca/project_about/', permanent=False), name="project_about_ca"),
    path('project_about/en/', RedirectView.as_view(url='/en/project_about/', permanent=False), name="project_about_en"),
    path('project_about/de/', RedirectView.as_view(url='/de/project_about/', permanent=False), name="project_about_de"),
    path('project_about/sq/', RedirectView.as_view(url='/sq/project_about/', permanent=False), name="project_about_sq"),
    path('project_about/el/', RedirectView.as_view(url='/el/project_about/', permanent=False), name="project_about_el"),
    path('project_about/hu/', RedirectView.as_view(url='/hu/project_about/', permanent=False), name="project_about_hu"),
    path('project_about/pt/', RedirectView.as_view(url='/pt/project_about/', permanent=False), name="project_about_pt"),
    path('project_about/sl/', RedirectView.as_view(url='/sl/project_about/', permanent=False), name="project_about_sl"),
    path('project_about/bg/', RedirectView.as_view(url='/bg/project_about/', permanent=False), name="project_about_bg"),
    path('project_about/ro/', RedirectView.as_view(url='/ro/project_about/', permanent=False), name="project_about_ro"),
    path('project_about/hr/', RedirectView.as_view(url='/hr/project_about/', permanent=False), name="project_about_hr"),
    path('project_about/mk/', RedirectView.as_view(url='/mk/project_about/', permanent=False), name="project_about_mk"),
    path('project_about/sr/', RedirectView.as_view(url='/sr/project_about/', permanent=False), name="project_about_sr"),
    path('project_about/lb/', RedirectView.as_view(url='/lb/project_about/', permanent=False), name="project_about_lb"),
    path('project_about/nl/', RedirectView.as_view(url='/nl/project_about/', permanent=False), name="project_about_nl"),
    path('project_about/tr/', RedirectView.as_view(url='/tr/project_about/', permanent=False), name="project_about_tr"),
    path('project_about/bn/', RedirectView.as_view(url='/bn/project_about/', permanent=False), name="project_about_bn"),
    path('project_about/sv/', RedirectView.as_view(url='/sv/project_about/', permanent=False), name="project_about_sv"),
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
    path('about_us/', show_about_us, name='help.show_about_us'),
    path('project_about/', show_project_about, name='help.show_project_about'),
    path('app_license/', show_app_license, name='help.show_app_license'),
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

    path('stats/report_stats_ccaa/', report_stats_ccaa, name='report_stats_ccaa'),
    path('stats/report_stats_ccaa_pie/', report_stats_ccaa_pie, name='report_stats_ccaa_pie'),
    path('stats/report_stats_ccaa_pie_sites/', report_stats_ccaa_pie_sites, name='report_stats_ccaa_pie_sites'),
    path('stats/report_stats/', report_stats, name='report_stats'),
    path('stats/registration_stats/', registration_stats, name='registration_stats'),
    path('stats/mosquito_ccaa_rich/<category>', mosquito_ccaa_rich, name='mosquito_ccaa_rich'),
    path('stats/mosquito_ccaa_rich_iframetest/', mosquito_ccaa_rich_iframetest, name='mosquito_ccaa_rich_iframetest'),
    path('stats/mosquito_ccaa_rich_iframetest_sites/', mosquito_ccaa_rich_iframetest_sites,name='mosquito_ccaa_rich_iframetest_sites'),
    path('stats/speedmeter/', speedmeter, name='speedmeter'),
    path('stats/adult_sunburst/', adult_sunburst, name='adult_sunburst'),
    path('stats/site_sunburst/', site_sunburst, name='site_sunburst'),
    path('stats/hashtag_map/', hashtag_map, name='hashtag_map'),
    path('stats/directory/', stats_directory, name='stats_directory'),
    path('stats/expert_report_assigned/', expert_report_assigned_data, name='expert_report_assigned_data'),
    path('stats/user_score/<user_uuid>', stats_user_score, name='stats_user_score'),
    path('stats/user_ranking/<page>', stats_user_ranking, name='stats_user_ranking'),
    path('stats/user_ranking/<page>/<user_uuid>', stats_user_ranking, name='stats_user_ranking'),

    path('experts/', expert_report_annotation, name='expert_report_annotation'),
    path('experts/geo_report_assign/', expert_geo_report_assign, name='expert_geo_report_assign'),
    path('experts/report_expiration/', report_expiration, name='report_expiration'),
    path('experts/report_expiration/<int:country_id>/', report_expiration, name='report_expiration'),
    path('experts/predefined_messages/', predefined_messages, name='predefined_messages'),
    path('entolab_license_agreement/', entolab_license_agreement, name='entolab_license_agreement'),
    path('experts/status/reports/', expert_report_status, name='expert_report_status'),
    path('experts/status/reports/pending', expert_report_pending, name='expert_report_pending'),
    path('experts/status/reports/complete', expert_report_complete, name='expert_report_complete'),
    path('experts/status/reports/single/<version_uuid>/', single_report_view, name='single_report_view'),
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
    # We do not include the message urls because two of the views (compose_w_data and reply_w_data) are slightly customized
    #url(r'^messages/', include('django_messages.urls')),
    #url(r'^$', RedirectView.as_view(permanent=True, url='inbox/'), name='messages_redirect'),
    path('messages/inbox/', inbox, name='messages_inbox'),
    path('messages/outbox/', outbox, name='messages_outbox'),
    path('messages/compose/', compose, name='messages_compose'),
    path('messages/compose/<recipient>/', compose, name='messages_compose_to'),
    path('messages/view/<int:message_id>/', view, name='messages_detail'),
    path('messages/delete/<int:message_id>/', delete, name='messages_delete'),
    path('messages/undelete/<int:message_id>/', undelete, name='messages_undelete'),
    path('messages/trash/', trash, name='messages_trash'),
    path('messages/compose_w_data/', compose_w_data, name='compose_w_data'),
    path('messages/reply/<int:message_id>/', reply_w_data, name='messages_reply'),
    path('jsi18n/', JavaScriptCatalog.as_view(), name='javascript-catalog'),
    path('metadataPhotoInfo', metadataPhoto, name='metadataPhotoInfo'),


)
