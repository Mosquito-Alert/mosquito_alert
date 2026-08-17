from drf_spectacular.helpers import lazy_serializer
from drf_spectacular.utils import extend_schema_field
from rest_framework import serializers

from mosquito_alert.taxa.models import Taxon


class SimpleTaxonSerializer(serializers.ModelSerializer):
    rank = serializers.ChoiceField(
        choices=[x.lower() for x in Taxon.TaxonomicRank.names]
    )

    italicize = serializers.SerializerMethodField(
        help_text="Display the name in italics when rendering."
    )

    def get_italicize(self, obj) -> bool:
        return obj.italicize

    def to_representation(self, instance):
        ret = super().to_representation(instance)
        ret["rank"] = [
            x.name.lower() for x in Taxon.TaxonomicRank if x.value == instance.rank
        ][0]
        return ret

    class Meta:
        model = Taxon
        fields = ("id", "name", "common_name", "rank", "italicize")
        extra_kwargs = {"id": {"read_only": True}}


class TaxonSerializer(SimpleTaxonSerializer):
    class Meta(SimpleTaxonSerializer.Meta):
        fields = SimpleTaxonSerializer.Meta.fields + ("is_relevant",)
        extra_kwargs = {"is_relevant": {"required": True}}


class TaxonTreeNodeSerializer(TaxonSerializer):
    children = serializers.SerializerMethodField()

    @extend_schema_field(
        lazy_serializer("mosquito_alert.api.v1.serializers.TaxonTreeNodeSerializer")(
            many=True
        )
    )
    def get_children(self, obj: Taxon):
        if obj.get_children_count():
            # TODO: get_children() -> can be improved to reduce the number of queries.
            return TaxonTreeNodeSerializer(obj.get_children(), many=True).data
        else:
            return []

    class Meta(TaxonSerializer.Meta):
        fields = TaxonSerializer.Meta.fields + ("children",)
