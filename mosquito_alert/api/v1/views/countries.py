from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from mosquito_alert.api.v1.permissions import CountriesPermissions
from mosquito_alert.api.v1.serializers.countries import CountrySerializer
from mosquito_alert.geo.models import Country

from mosquito_alert.api.v1.viewsets import GenericViewSet


@method_decorator(cache_page(12 * 60 * 60), name="list")  # cache for 12 hours
@method_decorator(cache_page(12 * 60 * 60), name="retrieve")  # cache for 12 hours
class CountriesViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    queryset = Country.objects.all()
    serializer_class = CountrySerializer
    permission_classes = (CountriesPermissions,)

    lookup_url_kwarg = "id"
