from django.conf.urls import patterns, url, include
from tigamap import views


urlpatterns = patterns('',
    url(r'^embedded/$', views.show_embedded_webmap, name='show_embedded_webmap'),
    url(r'^embedded/ca/$', views.show_embedded_webmap, name='show_embedded_webmap'),
    url(r'^embedded/es/$', views.show_embedded_webmap, name='show_embedded_webmap'),
    url(r'^embedded/en/$', views.show_embedded_webmap, name='show_embedded_webmap'),
    url(r'^ca/$', views.show_webmap_app, name='show_webmap_app'),
    url(r'^es/$', views.show_webmap_app, name='show_webmap_app'),
    url(r'^en/$', views.show_webmap_app, name='show_webmap_app'),
    url(r'^testingzone/coverage/$', views.show_coverage_map, name='show_coverage_map'),
    url(r'^testingzone/reports/$', views.show_report_map, name='show_report_map'),
    url(r'^$', views.show_webmap_app, name='show_webmap_app'),
)