from rest_framework.viewsets import ReadOnlyModelViewSet

from mosquito_alert.api.v1.serializers.partners import PartnerSerializer
from mosquito_alert.api.v1.views.viewsets import GenericViewSet
from mosquito_alert.partners.models import OrganizationPin


class PartnersViewSet(ReadOnlyModelViewSet, GenericViewSet):
    queryset = OrganizationPin.objects.all()
    serializer_class = PartnerSerializer
