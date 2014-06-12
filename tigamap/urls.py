from django.conf.urls import patterns, url, include
from tigamap import views


urlpatterns = patterns('',
    url(r'^embedded/(?P<language>\w+)$', views.show_embedded_webmap, name='webmap.show_embedded_webmap'),
    url(r'^embedded/$', views.show_embedded_webmap),
    url(r'^(?P<language>\w+)/$', views.show_webmap_app, name='webmap.show_webmap_app'),
    url(r'^$', views.show_webmap_app),
    url(r'^beta/(?P<report_type>\w+)/(?P<category>\w+)/$', views.show_map, name='webmap.show_map'),
    url(r'^beta/(?P<report_type>\w+)/$', views.show_map),
    url(r'^beta/$', views.show_map),
)

