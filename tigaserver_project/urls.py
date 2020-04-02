from django.conf.urls import *
from django.conf.urls.i18n import i18n_patterns
from django.views.generic.base import RedirectView

from django.contrib.gis import admin

from django.conf import settings
from django.conf.urls.static import static
from tigahelp.views import show_help, show_about, show_license, show_policies, show_terms, show_privacy, show_credit_image
from tigamap.views import show_filterable_report_map, show_single_report_map
from stats.views import show_usage, workload_stats, report_stats, registration_stats, report_stats_ccaa, report_stats_ccaa_pie, \
    report_stats_ccaa_pie_sites, mosquito_ccaa_rich, mosquito_ccaa_rich_iframetest, mosquito_ccaa_rich_iframetest_sites, speedmeter, stats_directory, \
    adult_sunburst, site_sunburst, hashtag_map
from tigaserver_app.views import lookup_photo
from tigacrafting.views import expert_report_annotation, expert_report_status, expert_status, picture_validation, notifications, single_report_view, metadataPhoto
from tigaserver_messages.views import compose_w_data, reply_w_data, compose
from django_messages.views import view,delete,undelete,trash,inbox,outbox
from django.contrib.auth import views as auth_views

from django.urls import include,path

admin.autodiscover()

urlpatterns = [
    path('admin/', admin.site.urls),
    path('api-auth/', include('rest_framework.urls', namespace='rest_framework')),
    path('api/', include('tigaserver_app.urls')),
    path('help/<platform>/<language>/', show_help),
    path('about/<platform>/<language>/', show_about),
    path('credits/', show_credit_image, name='show_credit_image'),
    path('license/<platform>/<language>/', show_license),
    path('i18n/', include('django.conf.urls.i18n')),
    path('webmap/embedded/ca/', RedirectView.as_view(url='/ca/webmap/embedded/', permanent=False)),
    path('webmap/embedded/es/', RedirectView.as_view(url='/es/webmap/embedded/', permanent=False)),
    path('webmap/embedded/en/', RedirectView.as_view(url='/en/webmap/embedded/', permanent=False)),
    path('webmap/ca/', RedirectView.as_view(url='/ca/webmap/', permanent=False)),
    path('webmap/es/', RedirectView.as_view(url='/es/webmap/', permanent=False)),
    path('webmap/en/', RedirectView.as_view(url='/en/webmap/', permanent=False)),
    path('policies/es/', RedirectView.as_view(url='/es/policies/', permanent=False)),
    path('policies/ca/', RedirectView.as_view(url='/ca/policies/', permanent=False)),
    path('policies/en/', RedirectView.as_view(url='/en/policies/', permanent=False)),
    path('policies/zh-cn/', RedirectView.as_view(url='/zh-cn/policies/', permanent=False)),
    path('terms/es/', RedirectView.as_view(url='/es/terms/', permanent=False)),
    path('terms/ca/', RedirectView.as_view(url='/ca/terms/', permanent=False)),
    path('terms/en/', RedirectView.as_view(url='/en/terms/', permanent=False)),
    path('terms/zh-cn/', RedirectView.as_view(url='/zh-cn/terms/', permanent=False)),
    path('privacy/es/', RedirectView.as_view(url='/es/privacy/', permanent=False)),
    path('privacy/ca/', RedirectView.as_view(url='/ca/privacy/', permanent=False)),
    path('privacy/en/', RedirectView.as_view(url='/en/privacy/', permanent=False)),
    path('privacy/zh-cn/', RedirectView.as_view(url='/zh-cn/privacy/', permanent=False)),
    path('tigapublic/', include('tigapublic.urls')),
    path('get_photo/<token>/<photo_uuid>/<size>', lookup_photo),
]

urlpatterns += static(settings.STATIC_URL, document_root=settings.STATIC_ROOT) + static(settings.MEDIA_URL, document_root=settings.MEDIA_ROOT)

urlpatterns += i18n_patterns(
    path('policies/', show_policies, name='help.show_policies'),
    path('terms/', show_terms, name='help.show_terms'),
    path('privacy/', show_privacy, name='help.show_privacy'),
    path('webmap/embedded/', show_filterable_report_map, {'fullscreen': 'off', 'legend': 'on'}),
    path('webmap/adults/', show_filterable_report_map, {'map_type': 'adult'}, name='adult_map'),
    path('webmap/adults/<selected_validation>/', show_filterable_report_map, {'map_type': 'adult'},name='adult_map_type'),
    path('webmap/sites/', show_filterable_report_map, {'map_type': 'site'}, name='site_map'),
    path('webmap/sites/<selected_validation>/', show_filterable_report_map, {'map_type': 'site'}, name='site_map_type'),
    path('webmap/coverage/', show_filterable_report_map, {'map_type': 'coverage'}, name='coverage_map'),
    path('webmap/', show_filterable_report_map, name='webmap.show_map_defaults'),
    path('', RedirectView.as_view(url='/static/tigapublic/spain.html#/es/', permanent=False)),
    path('bcn/', show_filterable_report_map,{'min_lat': 41.321049, 'min_lon': 2.052380, 'max_lat': 41.468609, 'max_lon': 2.225610, 'min_zoom': 12,'max_zoom': 18}),
    path('single_report_map/<version_uuid>/', show_single_report_map, name='webmap.single_report'),
    path('stats/', show_usage, name='show_usage'),
    path('stats/workload/', workload_stats, name='workload_stats'),
    path('stats/report_stats_ccaa/', report_stats_ccaa, name='report_stats_ccaa'),
    path('stats/report_stats_ccaa_pie/', report_stats_ccaa_pie, name='report_stats_ccaa_pie'),
    path('stats/report_stats_ccaa_pie_sites/', report_stats_ccaa_pie_sites, name='report_stats_ccaa_pie_sites'),
    path('stats/report_stats/', report_stats, name='report_stats'),
    path('stats/registration_stats/', registration_stats, name='registration_stats'),
    path('stats/mosquito_ccaa_rich/<category>', mosquito_ccaa_rich, name='mosquito_ccaa_rich'),
    path('stats/mosquito_ccaa_rich_iframetest/', mosquito_ccaa_rich_iframetest, name='mosquito_ccaa_rich_iframetest'),
    path('stats/mosquito_ccaa_rich_iframetest_sites/', mosquito_ccaa_rich_iframetest_sites, name='mosquito_ccaa_rich_iframetest_sites'),
    path('stats/speedmeter/', speedmeter, name='speedmeter'),
    path('stats/adult_sunburst/', adult_sunburst, name='adult_sunburst'),
    path('stats/site_sunburst/', site_sunburst, name='site_sunburst'),
    path('stats/hashtag_map/', hashtag_map, name='hashtag_map'),
    path('stats/directory/', stats_directory, name='stats_directory'),
    path('experts/', expert_report_annotation, name='expert_report_annotation'),
    path('experts/status/reports/', expert_report_status, name='expert_report_status'),
    path('experts/status/reports/single/<version_uuid>/', single_report_view, name='single_report_view'),
    path('experts/status/people/', expert_status, name='expert_status'),
    path('photo_grid/', picture_validation, name='picture_validation'),
    path('notifications/', notifications, name='notifications'),
    path('accounts/login/', auth_views.LoginView.as_view(), name='login'),
    path('logout/', auth_views.LogoutView.as_view(), {'next_page': '/experts/'}, name='auth_logout'),
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
    path('metadataPhotoInfo', metadataPhoto, name='metadataPhotoInfo'),
)
'''
urlpatterns += i18n_patterns('',
    url(r'^policies/$', show_policies, name='help.show_policies'),
    url(r'^terms/$', show_terms, name='help.show_terms'),
    url(r'^privacy/$', show_privacy, name='help.show_privacy'),
    url(r'^webmap/embedded/$', show_filterable_report_map, {'fullscreen': 'off', 'legend': 'on'}),
    url(r'^webmap/adults/$', show_filterable_report_map, {'map_type': 'adult'}, name='adult_map'),
    url(r'^webmap/adults/(?P<selected_validation>\w+)/$', show_filterable_report_map, {'map_type': 'adult'}, name='adult_map_type'),
    url(r'^webmap/sites/$', show_filterable_report_map, {'map_type': 'site'},  name='site_map'),
    url(r'^webmap/sites/(?P<selected_validation>\w+)/$', show_filterable_report_map,  {'map_type': 'site'}, name='site_map_type'),
    url(r'^webmap/coverage/$', show_filterable_report_map, {'map_type': 'coverage'}, name='coverage_map'),
    url(r'^webmap/$', show_filterable_report_map, name='webmap.show_map_defaults'),
    #url(r'^$', show_filterable_report_map, name='tigaserver_base_url'),
    url(r'^$', RedirectView.as_view(url='/static/tigapublic/spain.html#/es/', permanent=False)),
    url(r'^bcn/$', show_filterable_report_map, {'min_lat': 41.321049, 'min_lon': 2.052380, 'max_lat': 41.468609, 'max_lon':2.225610, 'min_zoom': 12, 'max_zoom': 18}),
    url(r'^single_report_map/(?P<version_uuid>[-\w]+)/$', show_single_report_map, name='webmap.single_report'),
    url(r'^stats/$', show_usage, name='show_usage'),
    url(r'^stats/workload/$', workload_stats, name='workload_stats'),
    url(r'^stats/report_stats_ccaa/$', report_stats_ccaa, name='report_stats_ccaa'),
    url(r'^stats/report_stats_ccaa_pie/$', report_stats_ccaa_pie, name='report_stats_ccaa_pie'),
    url(r'^stats/report_stats_ccaa_pie_sites/$', report_stats_ccaa_pie_sites, name='report_stats_ccaa_pie_sites'),
    url(r'^stats/report_stats/$', report_stats, name='report_stats'),
    url(r'^stats/registration_stats/$', registration_stats, name='registration_stats'),
    url(r'^stats/mosquito_ccaa_rich/(?P<category>\w+)$', mosquito_ccaa_rich, name='mosquito_ccaa_rich'),
    url(r'^stats/mosquito_ccaa_rich_iframetest/$', mosquito_ccaa_rich_iframetest, name='mosquito_ccaa_rich_iframetest'),
    url(r'^stats/mosquito_ccaa_rich_iframetest_sites/$', mosquito_ccaa_rich_iframetest_sites, name='mosquito_ccaa_rich_iframetest_sites'),
    url(r'^stats/speedmeter/$', speedmeter, name='speedmeter'),
    url(r'^stats/adult_sunburst/$', adult_sunburst, name='adult_sunburst'),
    url(r'^stats/site_sunburst/$', site_sunburst, name='site_sunburst'),
    url(r'^stats/hashtag_map/$', hashtag_map, name='hashtag_map'),
    url(r'^stats/directory/$', stats_directory, name='stats_directory'),
    #url(r'^reportstats/$', show_report_users),
    #url(r'^movelab_annotation/$', movelab_annotation, name='movelab_annotation'),
    #url(r'^movelab_annotation/(?P<tasks_per_page>[0-9]+)/$', movelab_annotation, name='movelab_annotation_tasks_per_page'),
    #url(r'^movelab_annotation/(?P<tasks_per_page>[0-9]+)/(?P<scroll_position>\w+)/$', movelab_annotation, name='movelab_annotation_scroll_position'),
    #url(r'^movelab_annotation_pending/$', movelab_annotation_pending, name='movelab_annotation_pending'),
    #url(r'^movelab_annotation_pending/(?P<tasks_per_page>[0-9]+)/$', movelab_annotation_pending,name='movelab_annotation_pending_tasks_per_page'),
    #url(r'^movelab_annotation_pending/(?P<tasks_per_page>[0-9]+)/(?P<scroll_position>\w+)/$', movelab_annotation_pending,name='movelab_annotation_pending_scroll_position'),

    url(r'^experts/$', expert_report_annotation, name='expert_report_annotation'),
    url(r'^experts/status/reports/$', expert_report_status, name='expert_report_status'),
    url(r'^experts/status/reports/single/(?P<version_uuid>[-\w]+)/$', single_report_view, name='single_report_view'),
    url(r'^experts/status/people/$', expert_status, name='expert_status'),
    url(r'^photo_grid/$', picture_validation, name='picture_validation'),
    url(r'^notifications/$', notifications, name='notifications'),

    ## should stay out
    #url(r'^coveragestats/$', show_fix_users),

    url(r'^accounts/login/$', 'django.contrib.auth.views.login', name='login'),
    #url(r'^processing/$', show_processing),
    url(r'^logout/$', 'django.contrib.auth.views.logout', {'next_page': '/experts/'}, name='auth_logout'),
    # We do not include the message urls because two of the views (compose_w_data and reply_w_data) are slightly customized
    #url(r'^messages/', include('django_messages.urls')),
    #url(r'^$', RedirectView.as_view(permanent=True, url='inbox/'), name='messages_redirect'),
    url(r'^messages/inbox/$', inbox, name='messages_inbox'),
    url(r'^messages/outbox/$', outbox, name='messages_outbox'),
    url(r'^messages/compose/$', compose, name='messages_compose'),
    url(r'^messages/compose/(?P<recipient>[\w.@+-]+)/$', compose, name='messages_compose_to'),
    #url(r'^reply/(?P<message_id>[\d]+)/$', reply, name='messages_reply'),
    url(r'^messages/view/(?P<message_id>[\d]+)/$', view, name='messages_detail'),
    url(r'^messages/delete/(?P<message_id>[\d]+)/$', delete, name='messages_delete'),
    url(r'^messages/undelete/(?P<message_id>[\d]+)/$', undelete, name='messages_undelete'),
    url(r'^messages/trash/$', trash, name='messages_trash'),
    url(r'^messages/compose_w_data/$', compose_w_data, name='compose_w_data'),
    url(r'^messages/reply/(?P<message_id>[\d]+)/$', reply_w_data, name='messages_reply'),
    url('metadataPhotoInfo', metadataPhoto, name='metadataPhotoInfo'),
)
'''