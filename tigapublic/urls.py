from django.conf.urls import patterns, url
from . import views

urlpatterns = patterns('',

    url(r'map_aux_reports_export\.(?P<format>(xls)|(csv))$',
        views.MapAuxReportsExportView.as_view()),

    url(r'map_aux_reports_zoom_bounds/(?P<zoom>[0-9]+)/(?P<bounds>[0-9.,-]+)$',
        views.map_aux_reports_zoom_bounds),

    url(r'map_aux_reports_bounds/(?P<bounds>[0-9.,-]+)$',
        views.map_aux_reports_bounds),

    url(r'map_aux_reports/(?P<id>[0-9]+)$',
        views.map_aux_reports),

    url(r'^ajax_login/$', views.ajax_login),
    url(r'^ajax_is_logged/$', views.ajax_is_logged),
    url(r'^ajax_logout/$', views.ajax_logout),

)
