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
    url(r'^testingzone/coverage25/$', views.show_coverage_map_25, name='show_coverage_map_25'),
    url(r'^testingzone/reports/$', views.show_report_map, name='show_report_map'),
    url(r'^testingzone/grid.05/$', views.show_grid_05, name='show_grid_05'),
    url(r'^testingzone/grid.1/$', views.show_grid_1, name='show_grid_1'),
    url(r'^testingzone/grid.25/$', views.show_grid_25, name='show_grid_25'),
    url(r'^testingzone/grid.5/$', views.show_grid_5, name='show_grid_5'),
    url(r'^$', views.show_webmap_app, name='show_webmap_app'),
)