from django.urls import path, include
from django.views.generic.base import RedirectView

# NOTE: needed for django-hosts
urlpatterns = [
    path('v1/', include(('api.urls', 'api'), namespace='v1')),  # Routes for API v1
    path('', RedirectView.as_view(url='/v1/', permanent=False)),
]