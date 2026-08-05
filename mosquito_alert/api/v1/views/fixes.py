from rest_framework.mixins import CreateModelMixin
from rest_framework.viewsets import GenericViewSet

from mosquito_alert.api.v1.serializers.fixes import FixSerializer
from mosquito_alert.fixes.models import Fix


class FixViewSet(CreateModelMixin, GenericViewSet):
    queryset = Fix.objects.all()
    serializer_class = FixSerializer
