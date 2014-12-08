from django.conf.urls import patterns, url, include
from rest_framework import routers
from tigaserver_app import views


router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'reports', views.ReportViewSet)
router.register(r'missions', views.MissionViewSet)
router.register(r'photos', views.PhotoViewSet)
router.register(r'fixes', views.FixViewSet)
router.register(r'configuration', views.ConfigurationViewSet)
router.register(r'map_data', views.MapDataViewSet)



urlpatterns = patterns('tigaserver_app.views',
    url(r'^time_info/$', 'get_data_time_info'),
    url(r'^photos/$', 'post_photo'),
    url(r'^configuration/$', 'get_current_configuration'),
    url(r'^missions/$', 'get_new_missions'),
    url(r'^', include(router.urls)),
)