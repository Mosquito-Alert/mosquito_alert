from django.urls import path

from .views import (
    show_usage,
    workload_stats,
    stats_user_score,
    stats_user_ranking,
    global_assignments,
    global_assignments_list
)

urlpatterns = [
    path('', show_usage, name='show_usage'),
    path('workload/', workload_stats, name='workload_stats'),
    path('workload/<country_id>/', workload_stats, name='workload_stats'),
    path('global_assignments/', global_assignments, name='global_assignments'),
    path('global_assignments_list/<country_code>/<status>/', global_assignments_list, name='global_assignments_list'),
    path('user_score/<user_uuid>', stats_user_score, name='stats_user_score'),
    path('user_ranking/<page>', stats_user_ranking, name='stats_user_ranking'),
    path('user_ranking/<page>/<user_uuid>', stats_user_ranking, name='stats_user_ranking'),
]