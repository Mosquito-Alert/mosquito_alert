from django.conf.urls import patterns, url, include
from tigahelp import views


urlpatterns = patterns('',
    url(r'^android/ca/$', views.show_help_ca, name='show_help_ca'),
    url(r'^android/es/$', views.show_help_es, name='show_help_es'),
    url(r'^android/en/$', views.show_help_en, name='show_help_en'),
    url(r'^ios/ca/$', views.show_help_ca, name='show_help_ca'),
    url(r'^ios/es/$', views.show_help_es, name='show_help_es'),
    url(r'^ios/en/$', views.show_help_en, name='show_help_en'),

)