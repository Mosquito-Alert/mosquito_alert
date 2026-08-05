from rest_framework.mixins import ListModelMixin, RetrieveModelMixin

from mosquito_alert.api.v1.views.viewsets import GenericViewSet
from mosquito_alert.campaigns.models import OWCampaigns
from mosquito_alert.api.v1.serializers.campaigns import CampaignSerializer
from mosquito_alert.api.v1.filters import CampaignFilter
from django_filters.rest_framework import DjangoFilterBackend


class CampaignsViewSet(RetrieveModelMixin, ListModelMixin, GenericViewSet):
    queryset = OWCampaigns.objects.all()
    serializer_class = CampaignSerializer

    filter_backends = (DjangoFilterBackend,)
    filterset_class = CampaignFilter
