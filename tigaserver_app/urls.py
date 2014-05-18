from django.conf.urls import patterns, url, include
from rest_framework import routers
from tigaserver_app import views


router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'reports', views.ReportViewSet)
router.register(r'report_responses', views.ReportItemViewSet)
router.register(r'missions', views.MissionViewSet)
router.register(r'photos', views.PhotoViewSet)
router.register(r'fixes', views.FixViewSet)
router.register(r'configurations', views.ConfigurationViewSet)



urlpatterns = patterns('tigaserver_app.views',
    url(r'^photos/$', 'upload_form'),
    url(r'^', include(router.urls)),
)