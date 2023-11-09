from __future__ import annotations

import typing

from django.db.models import QuerySet

from mosquito_alert.geo.models import Boundary

if typing.TYPE_CHECKING:
    from .models import SpecieDistribution


class SpecieDistributionQuerySet(QuerySet):
    def get_tree_for_instance(self, instance: SpecieDistribution, include_taxon_descendants: bool = True):
        from mosquito_alert.taxa.models import Taxon

        return self.filter(
            boundary__in=Boundary.get_tree(parent=instance.boundary),
            taxon__in=Taxon.get_tree(parent=instance.taxon) if include_taxon_descendants else [instance.taxon],
            source=instance.source,
        )

    def get_descendants_for_instance(self, instance: SpecieDistribution, include_taxon_descendants: bool = True):
        return self.get_tree_for_instance(
            instance=instance, include_taxon_descendants=include_taxon_descendants
        ).exclude(pk=instance.pk)

    def get_children_for_instance(self, instance: SpecieDistribution, include_taxon_descendants: bool = True):
        return self.get_descendants_for_instance(
            instance=instance, include_taxon_descendants=include_taxon_descendants
        ).filter(boundary__depth=instance.boundary.get_depth() + 1)

    def get_leaves_for_instance(self, instance: SpecieDistribution, include_taxon_descendants: bool = True):
        return self.get_tree_for_instance(
            instance=instance, include_taxon_descendants=include_taxon_descendants
        ).filter(boundary__numchild=0)
