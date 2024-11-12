from django.conf.urls import include
from django.urls import path, re_path
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
# router.register(r'all_reports', views.AllReportsMapViewSet, base_name='all_reports')
# router.register(r'all_reports_paginated', views.AllReportsMapViewSetPaginated, base_name='all_reports_paginated')
router.register(r'ack_notif', views.AcknowledgedNotificationViewSetPaginated, base_name='ack_notif')
# This is no longer used, see path('hidden_reports/', views.non_visible_reports),
# This line caused the NonVisibleReportsMapViewSet to be executed on app start. This is avoided
# by using the new non_visible_reports endpoint, which does exactly the same
#router.register(r'hidden_reports', views.NonVisibleReportsMapViewSet, base_name='hidden_reports')
router.register(r'owcampaigns', views.OWCampaignsViewSet, base_name='owcampaigns')
router.register(r'organizationpins', views.OrganizationsPinViewSet, base_name='organizationpins')
# There was some sort of uncontrolled caching happening here. To avoid it, I build the resultset
# record by record. This is slower. I don't care.
#router.register(r'cfa_reports', views.CoarseFilterAdultReports, base_name='cfa_reports')
#router.register(r'cfs_reports', views.CoarseFilterSiteReports, base_name='cfs_reports')
router.register(r'tags', views.TagViewSet, base_name='tags')

urlpatterns = [
    path('all_reports/', views.all_reports),
    path('all_reports_paginated/', views.all_reports_paginated),
    path('hidden_reports/', views.non_visible_reports),
    path('hidden_reports_paginated/', views.non_visible_reports_paginated),
    # This is disabled, we do not give users the chance to flip crisis mode
    #path('toggle_crisis/(?P<user_id>\d+)/', views.toggle_crisis_mode),
    re_path('crisis_report_assign/(?P<user_id>\d+)/(?P<country_id>\d+)/', views.crisis_report_assign),
    path('mark_notif_as_ack/', views.mark_notif_as_ack),
    path('subscribe_to_topic/', views.subscribe_to_topic),
    path('unsub_from_topic/', views.unsub_from_topic),
    path('topics_subscribed/', views.topics_subscribed),
    path('photo_blood/', views.photo_blood),
    path('photo_blood_reset/', views.photo_blood_reset),
    path('time_info/', views.get_data_time_info),
    path('score_v2/', views.user_score_v2),
    path('photos/', views.post_photo),
    path('photos_user/', views.get_photo),
    path('configuration/', views.get_current_configuration),
    path('user_notifications/', views.user_notifications),
    path('notification_content/', views.notification_content),
    path('send_notifications/', views.send_notifications),
    path('report_stats/', views.report_stats),
    path('user_count/', views.user_count),
    path('user_score/', views.user_score),
    path('token/', views.token),
    path('msg_ios/', views.msg_ios),
    path('msg_android/', views.msg_android),
    path('nearby_reports/', views.nearby_reports),
    path('nearby_reports_fast/', views.nearby_reports_fast),
    path('nearby_reports_nod/', views.nearby_reports_no_dwindow),
    path('reports_id_filtered/', views.reports_id_filtered),
    path('uuid_list_autocomplete/', views.uuid_list_autocomplete),
    path('missions/', views.get_new_missions),
    path('cfs_reports/', views.force_refresh_cfs_reports),
    path('cfa_reports/', views.force_refresh_cfa_reports),
    re_path('clear_blocked/(?P<username>[\w.@+-]+)/', views.clear_blocked),
    re_path('clear_blocked_r/(?P<username>[\w.@+-]+)/(?P<report>[\w-]+)/', views.clear_blocked),
    path('clear_blocked_all/', views.clear_blocked_all),
    re_path('session_update/(?P<pk>\d+)/', views.SessionPartialUpdateView.as_view(), name="session_update"),
    path('stats/workload_data/user/', workload_stats_per_user),
    path('stats/workload_data/report_input/', workload_daily_report_input),
    path('stats/workload_data/pending/', workload_pending_per_user),
    path('stats/workload_data/available/', workload_available_reports),
    path('stats/speedmeter/', speedmeter_api),
    path('stats/hashtag_map_data/', get_hashtag_map_data),
    path('stats/user_xp_data/', get_user_xp_data),
    path('favorite/', views.favorite),
    path('user_favorites/', views.user_favorites),
    path('coarse_filter_reports/', views.coarse_filter_reports),
    path('annotate_coarse/', views.annotate_coarse),
    path('hide_report/', views.hide_report),
    path('flip_report/', views.flip_report),
    path('quick_upload_report/', views.quick_upload_report),
    path('', include(router.urls)),
]