from django.conf.urls import include
from django.urls import path, re_path
from rest_framework import routers
from tigaserver_app import views
from stats.views import workload_stats_per_user,workload_daily_report_input,workload_pending_per_user,workload_available_reports, speedmeter_api, get_user_xp_data

router = routers.DefaultRouter()
router.register(r'users', views.UserViewSet)
router.register(r'addresses', views.UserAddressViewSet)
router.register(r'reports', views.ReportViewSet)
router.register(r'sessions', views.SessionViewSet)
router.register(r'photos', views.PhotoViewSet)
router.register(r'fixes', views.FixViewSet)
router.register(r'owcampaigns', views.OWCampaignsViewSet)
router.register(r'organizationpins', views.OrganizationsPinViewSet)
router.register(r'tags', views.TagViewSet)

urlpatterns = [
    re_path('crisis_report_assign/(?P<user_id>\d+)/(?P<country_id>\d+)/', views.crisis_report_assign),
    path('mark_notif_as_ack/', views.mark_notif_as_ack),
    path('subscribe_to_topic/', views.subscribe_to_topic),
    path('unsub_from_topic/', views.unsub_from_topic),
    path('topics_subscribed/', views.topics_subscribed),
    path('photo_blood/', views.photo_blood),
    path('photo_blood_reset/', views.photo_blood_reset),
    path('photos/', views.post_photo),
    path('user_notifications/', views.user_notifications),
    path('notification_content/', views.notification_content),
    path('send_notifications/', views.send_notifications),
    path('user_count/', views.user_count),
    path('token/', views.token),
    path('reports_id_filtered/', views.reports_id_filtered),
    path('uuid_list_autocomplete/', views.uuid_list_autocomplete),
    re_path('clear_blocked/(?P<username>[\w.@+-]+)/', views.clear_blocked),
    re_path('clear_blocked_r/(?P<username>[\w.@+-]+)/(?P<report>[\w-]+)/', views.clear_blocked),
    path('clear_blocked_all/', views.clear_blocked_all),
    re_path('session_update/(?P<pk>\d+)/', views.SessionPartialUpdateView.as_view(), name="session_update"),
    path('stats/workload_data/user/', workload_stats_per_user),
    path('stats/workload_data/report_input/', workload_daily_report_input),
    path('stats/workload_data/pending/', workload_pending_per_user),
    path('stats/workload_data/available/', workload_available_reports),
    path('stats/speedmeter/', speedmeter_api),
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