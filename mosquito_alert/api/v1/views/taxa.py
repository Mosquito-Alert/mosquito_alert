from django.utils.decorators import method_decorator
from django.views.decorators.cache import cache_page
from drf_spectacular.utils import extend_schema
from rest_framework.decorators import action
from rest_framework.mixins import ListModelMixin, RetrieveModelMixin
from rest_framework.permissions import IsAuthenticatedOrReadOnly
from rest_framework.response import Response

from mosquito_alert.api.v1.filters import TaxonFilter
from mosquito_alert.api.v1.serializers.taxa import (
    TaxonSerializer,
    TaxonTreeNodeSerializer,
)
from mosquito_alert.api.v1.views.viewsets import GenericViewSet
from mosquito_alert.taxa.models import Taxon


class TaxaViewSet(ListModelMixin, RetrieveModelMixin, GenericViewSet):
    queryset = Taxon.objects.all()
    serializer_class = TaxonSerializer
    filterset_class = TaxonFilter
    permission_classes = (IsAuthenticatedOrReadOnly,)

    @method_decorator(cache_page(6 * 60 * 60))  # cache for 6 hour
    def list(self, request, *args, **kwargs):
        return super().list(request, *args, **kwargs)

    @extend_schema(operation_id="taxa_root_tree_retrieve")
    @method_decorator(cache_page(6 * 60 * 60))  # cache for 6 hour
    @action(
        detail=False,
        methods=["GET"],
        url_path="tree",
        serializer_class=TaxonTreeNodeSerializer,
    )
    def root_tree(self, request):
        taxon = Taxon.get_root()
        serializer = self.get_serializer(taxon)
        return Response(serializer.data)

    @method_decorator(cache_page(6 * 60 * 60))  # cache for 6 hour
    @action(
        detail=True,
        methods=["GET"],
        url_path="tree",
        serializer_class=TaxonTreeNodeSerializer,
    )
    def tree(self, request, pk=None):
        taxon = self.get_object()
        serializer = self.get_serializer(taxon)
        return Response(serializer.data)
