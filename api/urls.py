from django.urls import path, re_path

from rest_framework import routers
from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView

from drf_spectacular.settings import spectacular_settings
from drf_spectacular.utils import extend_schema
from drf_spectacular.views import SpectacularRedocView, SpectacularAPIView, SpectacularJSONAPIView

from .views import (
    UserViewSet,
    FixViewSet,
    CampaignsViewSet,
    PartnersViewSet,
    CountriesViewSet,
    NotificationViewSet,
    PhotoViewSet,
    ObservationViewSest,
    BiteViewSet,
    BreedingSiteViewSet
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
router.register(r"bites", BiteViewSet)
router.register(r"breeding-sites", BreedingSiteViewSet)
router.register(r"campaigns", CampaignsViewSet)
router.register(r"countries", CountriesViewSet)
router.register(r"fixes", FixViewSet)
router.register(r"notifications", NotificationViewSet)
router.register(r"observations", ObservationViewSest)
router.register(r"partners", PartnersViewSet)
router.register(r"photos", PhotoViewSet)
router.register(r"users", UserViewSet)


api_urlpatterns = [
    path("token/", TokenObtainPairView.as_view(), name="token_obtain_pair"),
    path("token/refresh/", TokenRefreshView.as_view(), name="token_refresh"),
]

api_urlpatterns += router.urls

urlpatterns = [
    path("openapi.yml", SpectacularAPIView.as_view(), name="schema"),
    path("openapi.json", SpectacularJSONAPIView.as_view(), name="schema-json"),
    re_path("$^", CustomRedocView.as_view(url_name="schema"), name="redoc"),
] + api_urlpatterns
