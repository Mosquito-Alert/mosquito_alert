from ..models import GeoLocatedModel


class DummyGeoLocatedModel(GeoLocatedModel):
    class Meta(GeoLocatedModel.Meta):
        abstract = False
