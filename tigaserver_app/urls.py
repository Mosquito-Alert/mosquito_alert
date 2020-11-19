from django.conf.urls import url, include
from rest_framework import routers
from tigaserver_app import views
from stats.views import workload_stats_per_user,workload_daily_report_input,workload_pending_per_user,workload_available_reports, speedmeter_api, get_hashtag_map_data, get_user_xp_data

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'addresses', views.UserAddressViewSet)
router.register(r'reports', views.ReportViewSet)
router.register(r'sessions', views.SessionViewSet)
router.register(r'photos', views.PhotoViewSet)
router.register(r'fixes', views.FixViewSet)
router.register(r'coverage_month', views.CoverageMonthMapViewSet, base_name='coverage_month')
router.register(r'all_reports', views.AllReportsMapViewSet, base_name='all_reports')
router.register(r'all_reports_paginated', views.AllReportsMapViewSetPaginated, base_name='all_reports_paginated')
router.register(r'hidden_reports', views.NonVisibleReportsMapViewSet, base_name='hidden_reports')
# There was some sort of uncontrolled caching happening here. To avoid it, I build the resultset
# record by record. This is slower. I don't care.
#router.register(r'cfa_reports', views.CoarseFilterAdultReports, base_name='cfa_reports')
#router.register(r'cfs_reports', views.CoarseFilterSiteReports, base_name='cfs_reports')
router.register(r'tags', views.TagViewSet, base_name='tags')

urlpatterns = [
    url('time_info/$', views.get_data_time_info),
    url('score_v2/$', views.user_score_v2),
    url('photos/$', views.post_photo),
    url('photos_user/$', views.get_photo),
    url('configuration/$', views.get_current_configuration),
    url('user_notifications/$', views.user_notifications),
    url('notification_content/$', views.notification_content),
    url('send_notifications/$', views.send_notifications),
    url('report_stats/$', views.report_stats),
    url('user_count/$', views.user_count),
    url('user_score/$', views.user_score),
    url('token/$', views.token),
    url('msg_ios/$', views.msg_ios),
    url('msg_android/$', views.msg_android),
    url('nearby_reports/$', views.nearby_reports),
    url('nearby_reports_fast/$', views.nearby_reports_fast),
    url('nearby_reports_nod/$', views.nearby_reports_no_dwindow),
    url('reports_id_filtered/$', views.reports_id_filtered),
    url('uuid_list_autocomplete/$', views.uuid_list_autocomplete),
    url('missions/$', views.get_new_missions),
    url('cfs_reports/$', views.force_refresh_cfs_reports),
    url('cfa_reports/$', views.force_refresh_cfa_reports),
    url('profile/new/$', views.profile_new),
    url('profile/$', views.profile_detail),
    url('session_update/(?P<pk>\d+)/$', views.SessionPartialUpdateView.as_view(), name="session_update"),
    url('stats/workload_data/user/$', workload_stats_per_user),
    url('stats/workload_data/report_input/$', workload_daily_report_input),
    url('stats/workload_data/pending/$', workload_pending_per_user),
    url('stats/workload_data/available/$', workload_available_reports),
    url('stats/speedmeter/$', speedmeter_api),
    url('stats/hashtag_map_data/$', get_hashtag_map_data),
    url('stats/user_xp_data/$', get_user_xp_data),
    url('', include(router.urls)),
]