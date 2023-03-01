from django.db import models


class IdentificationResultManager(models.Manager):
    def get_consensus(self, individual, type, min_prob=0.75, min_taxon_rank=None):
        qs = self.filter(type=type, individual=individual, probability__gte=min_prob)
        if min_taxon_rank:
            qs = qs.filter(taxon__rank__gte=min_taxon_rank)

        return qs.last()


class ProxyIdentificationResultManager(IdentificationResultManager):
    def __init__(self, type, *args, **kwargs):
        self._type = type
        super().__init__(*args, **kwargs)

    def create(self, **kwargs):
        kwargs.update({"type": self._type})
        return super().create(**kwargs)

    def get_consensus(self, **kwargs):
        kwargs.update({"type": self._type})
        return super().get_consensus(**kwargs)

    def get_queryset(self):
        return super().get_queryset().filter(type=self._type)
