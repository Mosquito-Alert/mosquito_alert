from polymorphic.query import PolymorphicQuerySet

from mosquito_alert.geo.querysets import GeoLocatedModelQuerySet


class ReportQuerySet(PolymorphicQuerySet, GeoLocatedModelQuerySet):
    pass
