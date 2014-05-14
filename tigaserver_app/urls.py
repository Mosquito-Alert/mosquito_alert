from django.conf.urls import *
from tigaserver_app import views


urlpatterns = patterns('',
    url(r'^photos/upload/$', views.upload_photo, name='upload_photo'),
)




