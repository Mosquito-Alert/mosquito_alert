from django.db.models import Subquery

from mosquito_alert.geo.querysets import GeoLocatedPolymorphicModelQuerySet
from mosquito_alert.individuals.models import Individual
from mosquito_alert.moderation.querysets import FlagModeratedPolymorphicModelQuerySet


class ReportQueryset(GeoLocatedPolymorphicModelQuerySet, FlagModeratedPolymorphicModelQuerySet):
    def browsable(self):
        return self.filter(published=True).with_permitted_state()


class IndividualReportQueryset(ReportQueryset):
    def with_identified_taxon(self, taxon):
        individuals = Individual.objects.filter_by_taxon(taxon=taxon)
        return self.filter(individuals__in=Subquery(individuals.values("pk")))
