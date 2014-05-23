from django.conf.urls import patterns, url, include
from tigamap import views


urlpatterns = patterns('',
    url(r'^$', views.show_fixes, name='show_fixes'),
    url(r'^embedded/$', views.show_fixes, name='show_fixes'),
    url(r'^embedded/ca/$', views.show_fixes, name='show_fixes'),
    url(r'^embedded/es/$', views.show_fixes, name='show_fixes'),
    url(r'^embedded/en/$', views.show_fixes, name='show_fixes'),
    url(r'^ca/$', views.show_fixes, name='show_fixes'),
    url(r'^es/$', views.show_fixes, name='show_fixes'),
    url(r'^en/$', views.show_fixes, name='show_fixes'),
)