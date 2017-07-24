from django.conf.urls import patterns, url
from . import views

urlpatterns = patterns('',

    url(r'map_aux_reports_export\.(?P<format>(xls)|(csv))$',
        views.MapAuxReportsExportView.as_view()),

    url(r'map_aux_reports_zoom_bounds/(?P<zoom>[0-9]+)/(?P<bounds>[0-9.,-]+)$',
        views.map_aux_reports_zoom_bounds),
    url(r'map_aux_reports_bounds/(?P<bounds>[0-9.,-]+)/(?P<notifs>[n|N|0|1]+)/?P<hashtag>N$',
        views.map_aux_reports_bounds_notifs),
    url(r'map_aux_reports_bounds/(?P<bounds>[0-9.,-]+)/(?P<notifs>[n|N|0|1]+)/(?P<hashtag>[#0-9a-zA-Z]+)$',
        views.map_aux_reports_bounds_notifs_hashtag),
    url(r'get_reports_by_notif_type/(?P<bounds>[0-9.,-]+)/(?P<types>[,|n|N|0-9]+)/(?P<hashtag>[#0-9a-zA-Z]+)$',
        views.getReportsByNotifType),

    url(r'map_aux_reports_bounds/(?P<bounds>[0-9.,-]+)$',
        views.map_aux_reports_bounds),

    url(r'map_aux_reports/(?P<id>[0-9]+)$',
        views.map_aux_reports),

    url(r'^ajax_login/$', views.ajax_login),
    url(r'^ajax_is_logged/$', views.ajax_is_logged),
    url(r'^ajax_logout/$', views.ajax_logout),
    url(r'^userfixes/(.*)/(.*)$', views.userfixes),
    url(r'^reports/([0-9.,-]+)/(all|[0-9.,-]+)/(all|[0-9.,]+)/([a-zA-Z,_]+)/([0|1|2])/([#0-9a-zA-Z]+)/[nN]$', views.reports_notif),#this should go first
    #url(r'^reports/([0-9.,-]+)/(.*)/(.*)/(.*)/$', views.reports),
    url(r'^reports/([0-9.,-]+)/(all|[0-9.,-]+)/(all|[0-9.,]+)/([a-zA-Z,_]+)/[nN]/([#0-9a-zA-Z]+)/(n|N|[0-9,]+)$', views.reports),
    #TODO remove notifications functions from view.py
    #url(r'^notifications/(.*)/(.*)/(.*)$', views.notifications),
    url(r'^save_notification/$', views.save_notification),
    url(r'^imageupload/$', views.imageupload),
    url(r'^intersect/([a-zA-Z,_]+)/(all|[0-9.,]+)/(all|[0-9.,]+)/$', views.intersects),
    #url(r'^embornals/$', views.embornals),
    url(r'^embornals/$', views.getStormDrainData),
    url(r'^getStormDrainUserSetup/$', views.getStormDrainUserSetup),
    url(r'^put/style/version/$', views.putStormDrainStyle),
    url(r'^fileupload/$', views.stormDrainUpload),
    url(r'^stormdrain/get/template/$', views.getStormDrainTemplate),
    url(r'^getpredefinednotifications/$', views.getPredefinedNotifications),
    url(r'^getlistnotifications/$', views.getListNotifications)

)
