from django.urls import path
from .views import user_is_logged, ajax_login, ajax_logout, user_reports

urlpatterns = [
    path('user_is_logged', user_is_logged),
    path('ajax_login', ajax_login),
    path('ajax_logout', ajax_logout),
    path('user_reports', user_reports),
]