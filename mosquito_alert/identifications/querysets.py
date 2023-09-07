from django.db import models
from django.db.models.query import QuerySet

from .settings import MIN_CONSENSUS_PROB


class TaxonClassificationCandidateQuerySet(models.QuerySet):
    def get_consensus(self, min_prob: float = MIN_CONSENSUS_PROB, min_taxon_rank=None) -> models.QuerySet:
        qs = self.filter(probability__gte=min_prob)
        if min_taxon_rank:
            qs = qs.filter(label__rank__gte=min_taxon_rank)

        # NOTE: Will raise DoesNotExist if not found.
        return qs.latest("label__rank", "probability")


class BaseIdentificationQuerySet(QuerySet):
    def finished(self):
        return self


class UserIdentificationQuerySet(BaseIdentificationQuerySet):
    def finished(self):
        return self.filter(was_skipped=False)
