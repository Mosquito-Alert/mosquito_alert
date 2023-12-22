from django.conf.urls import url, include
from django.urls import path

from rest_framework import routers
from drf_yasg.views import get_schema_view
from drf_yasg import openapi

from .views import (
    UserViewSet,
    ReportViewSet,
    PhotoViewSet,
    FixViewSet,
    OWCampaignsViewSet,
    OrganizationPinViewSet,
)

# from django.http import HttpResponse
# TODO: depracate old API
# def your_endpoint(request):
#     # Your existing endpoint logic
#     response = HttpResponse("Your response content")
#     response['Deprecation-Notice'] = "This endpoint is deprecated, use ... instead."
#     return response

schema_view = get_schema_view(
    openapi.Info(
        title="Mosquito Alert API",
        default_version="v1",
        terms_of_service="https://webserver.mosquitoalert.com/es/terms/",  # TODO: use get_view
        contact=openapi.Contact(email="it@mosquitoalert.com"),
        license=openapi.License(name="GPL-3 License"),
    ),
    public=True,
)

router = routers.DefaultRouter()
router.register(r"users", UserViewSet)  # GET and POST

# router.register(r"addresses", UserAddressViewSet)  # Not used
router.register(r"reports", ReportViewSet)  # GET and POST
router.register(r"fixes", FixViewSet)  # GET and POST
# router.register(
#    r"coverage_month", CoverageMonthMapViewSet, base_name="coverage_month"
# )  # Not used
# router.register(
#    r"ack_notif", AcknowledgedNotificationViewSetPaginated, base_name="ack_notif"
# )  # Not used
router.register(r"owcampaigns", OWCampaignsViewSet, base_name="owcampaigns")  # GET
router.register(
    r"organizationpins", OrganizationPinViewSet, base_name="organizationpins"
)  # GET
# router.register(r"tags", TagViewSet, base_name="tags")  # Not used


urlpatterns = [
    url(r"", include(router.urls)),
    path(
        "docs/",
        schema_view.with_ui("swagger", cache_timeout=0),
        name="schema-swagger-ui",
    ),
]
