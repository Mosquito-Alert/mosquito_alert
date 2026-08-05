from rest_framework import serializers

from mosquito_alert.geo.models import Country


class CountrySerializer(serializers.ModelSerializer):
    class Meta:
        model = Country
        fields = ("id", "name_en", "iso3_code")
        extra_kwargs = {"name_en": {"source": "name_engl"}}
