from django.urls import path, include
from django.views.generic.base import RedirectView

urlpatterns = [
    path('v1/', include(('mosquito_alert.api.v1.urls', 'mosquito_alert.api'), namespace='v1')),  # Routes for API v1
    path('', RedirectView.as_view(pattern_name="v1:redoc", permanent=False)),
    path('', include(('mosquito_alert.api.v0.urls', 'mosquito_alert.api'), namespace='legacy')),
]