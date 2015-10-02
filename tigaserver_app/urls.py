from django.conf.urls import patterns, url, include
from rest_framework import routers
import tigaserver_app

router = routers.DefaultRouter()
router.register(r'users', tigaserver_app.views.UserViewSet)
router.register(r'reports', tigaserver_app.views.ReportViewSet)
router.register(r'photos', tigaserver_app.views.PhotoViewSet)
router.register(r'fixes', tigaserver_app.views.FixViewSet)
router.register(r'coverage_month', tigaserver_app.views.CoverageMonthMapViewSet, base_name='coverage_month')
router.register(r'all_reports', tigaserver_app.views.AllReportsMapViewSet, base_name='all_reports')

urlpatterns = patterns('',
    url(r'^time_info/$', 'tigaserver_app.views.get_data_time_info'),
    url(r'^photos/$', 'tigaserver_app.views.post_photo'),
    url(r'^configuration/$', 'tigaserver_app.views.get_current_configuration'),
    url(r'^missions/$', 'tigaserver_app.views.get_new_missions'),
    url(r'^', include(router.urls)),
)