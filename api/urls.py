from django.urls import path, re_path, include

from rest_framework_simplejwt.views import TokenObtainPairView, TokenRefreshView, TokenVerifyView
from rest_framework_nested import routers

from drf_spectacular.settings import spectacular_settings
from drf_spectacular.utils import extend_schema, extend_schema_view
from drf_spectacular.views import SpectacularRedocView, SpectacularAPIView, SpectacularJSONAPIView

from .auth.views import GuestRegisterView, PasswordChangeView
from .views import (
    UserViewSet,
    MyUserViewSet,
    FixViewSet,
    CampaignsViewSet,
    PartnersViewSet,
    CountriesViewSet,
    NotificationViewSet,
    MyNotificationViewSet,
    PhotoViewSet,
    ObservationViewSest,
    MyObservationViewSest,
    BiteViewSet,
    MyBiteViewSet,
    BreedingSiteViewSet,
    MyBreedingSiteViewSet,
    DeviceViewSet,
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


router = routers.SimpleRouter()
router.register(r"bites", BiteViewSet)
router.register(r"breeding-sites", BreedingSiteViewSet)
router.register(r"devices", DeviceViewSet)
router.register(r"campaigns", CampaignsViewSet)
router.register(r"countries", CountriesViewSet)
router.register(r"fixes", FixViewSet)
router.register(r"notifications", NotificationViewSet)
router.register(r"observations", ObservationViewSest)
router.register(r"partners", PartnersViewSet)
router.register(r"photos", PhotoViewSet)
router.register(r"users", UserViewSet)

token_obtain_view = TokenObtainPairView.as_view()
token_obtain_view = extend_schema_view(post=extend_schema(operation_id="auth_obtain_token"))(token_obtain_view)

token_refresh_view = TokenRefreshView.as_view()
token_refresh_view = extend_schema_view(post=extend_schema(operation_id="auth_refresh_token"))(token_refresh_view)

token_verify_view = TokenVerifyView.as_view()
token_verify_view = extend_schema_view(post=extend_schema(operation_id="auth_verify_token"))(token_verify_view)

api_urlpatterns = [
    path("auth/signup/guest/", GuestRegisterView.as_view(), name='guest-register'),
    path("auth/token/", token_obtain_view, name="token_obtain_pair"),
    path("auth/token/refresh/", token_refresh_view, name="token_refresh"),
    path("auth/token/verify/", token_verify_view, name="token_verify"),
    path("auth/password/change/", PasswordChangeView.as_view(), name='password-change'),
]

api_urlpatterns += [
    path("me/", MyUserViewSet.as_view({'get': 'retrieve'}), name='my-user'),
    path("me/notifications/", MyNotificationViewSet.as_view({'get': 'list'}), name='my-notifications'),
    path("me/observations/", MyObservationViewSest.as_view({'get': 'list'}), name='my-observations'),
    path("me/bites/", MyBiteViewSet.as_view({'get': 'list'}), name='my-bites'),
    path("me/breeding-sites/", MyBreedingSiteViewSet.as_view({'get': 'list'}), name='my-breeding-sites'),
]

api_urlpatterns += router.urls

urlpatterns = [
    path("", include(api_urlpatterns)),
    path("openapi.yml", SpectacularAPIView.as_view(api_version='v1'), name="schema"),
    path("openapi.json", SpectacularJSONAPIView.as_view(api_version='v1'), name="schema-json"),
    re_path("$^", CustomRedocView.as_view(url_name="schema"), name="redoc"),
]