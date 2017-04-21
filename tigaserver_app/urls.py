from django.conf.urls import patterns, url, include
from rest_framework import routers
from tigaserver_app import views

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'reports', views.ReportViewSet)
router.register(r'photos', views.PhotoViewSet)
router.register(r'fixes', views.FixViewSet)
router.register(r'coverage_month', views.CoverageMonthMapViewSet, base_name='coverage_month')
router.register(r'all_reports', views.AllReportsMapViewSet, base_name='all_reports')
router.register(r'hidden_reports', views.NonVisibleReportsMapViewSet, base_name='hidden_reports')
router.register(r'tags', views.TagViewSet, base_name='tags')

urlpatterns = patterns('',
    url(r'^time_info/$', views.get_data_time_info),
    url(r'^photos/$', views.post_photo),
    url(r'^photos_user/$', views.get_photo),
    url(r'^configuration/$', views.get_current_configuration),
    url(r'^user_notifications/$', views.user_notifications),
    url(r'^notification_content/$', views.notification_content),
    url(r'^send_notifications/$', views.send_notifications),
    url(r'^report_stats/$', views.report_stats),
    url(r'^user_count/$', views.user_count),
    url(r'^user_score/$', views.user_score),
    url(r'^token/$', views.token),
    url(r'^msg_ios/$', views.msg_ios),
    url(r'^msg_android/$', views.msg_android),
    url(r'^nearby_reports/$', views.nearby_reports),
    url(r'^missions/$', views.get_new_missions),
    url(r'^', include(router.urls)),
)