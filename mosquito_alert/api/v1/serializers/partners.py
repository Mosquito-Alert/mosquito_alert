from rest_framework import serializers
from drf_extra_fields.geo_fields import PointField

from mosquito_alert.partners.models import OrganizationPin


class PartnerSerializer(serializers.ModelSerializer):
    point = PointField(required=True)

    class Meta:
        model = OrganizationPin
        fields = ("id", "point", "description", "url")
        extra_kwargs = {
            "description": {"source": "textual_description"},
            "url": {"source": "page_url"},
        }
