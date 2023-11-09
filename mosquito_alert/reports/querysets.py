from mosquito_alert.geo.querysets import GeoLocatedPolymorphicModelQuerySet
from mosquito_alert.moderation.querysets import FlagModeratedPolymorphicModelQuerySet


class ReportQueryset(GeoLocatedPolymorphicModelQuerySet, FlagModeratedPolymorphicModelQuerySet):
    def browsable(self):
        return self.filter(published=True).with_permitted_state()
