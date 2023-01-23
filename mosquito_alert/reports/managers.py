from polymorphic.managers import PolymorphicManager

from mosquito_alert.geo.managers import GeoLocatedManager


class ReportManager(PolymorphicManager, GeoLocatedManager):
    pass
