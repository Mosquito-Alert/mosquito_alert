from django.conf.urls import patterns, url, include
from tigamap import views


urlpatterns = patterns('',
    url(r'^$', views.show_fixes, name='show_fixes')
)