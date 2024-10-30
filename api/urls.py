from django.urls import path, re_path

from rest_framework import routers
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from drf_spectacular.settings import spectacular_settings
from drf_spectacular.utils import extend_schema
from drf_spectacular.views import SpectacularRedocView, SpectacularAPIView

from .views import (
    UserViewSet,
    ReportViewSet,
    FixViewSet,
    CampaignsViewSet,
    PartnersViewSet,
    CountriesViewSet,
    NotificationViewSet,
    PhotoViewSet,
)


class CustomRedocView(SpectacularRedocView):
    template_name = "api/redoc.html"

    @extend_schema(exclude=True)
    def get(self, request, *args, **kwargs):
        response = super().get(request, *args, **kwargs)
        response.data["description"] = spectacular_settings.DESCRIPTION
        response.data["request"] = request
        response.data["version"] = request.version or request.GET.get("version")

        return response


router = routers.DefaultRouter()
router.register(r"campaigns", CampaignsViewSet)
router.register(r"countries", CountriesViewSet)
router.register(r"fixes", FixViewSet)
router.register(r"notifications", NotificationViewSet)
router.register(r"partners", PartnersViewSet)
router.register(r"photos", PhotoViewSet)
router.register(r"reports", ReportViewSet)
router.register(r"users", UserViewSet)


api_urlpatterns = [
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]

api_urlpatterns += router.urls

urlpatterns = [
    path("schema/", SpectacularAPIView.as_view(), name="schema"),
    re_path("$^", CustomRedocView.as_view(url_name="schema"), name="redoc"),
] + api_urlpatterns
