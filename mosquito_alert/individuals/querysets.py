from django.db import models

from mosquito_alert.taxa.models import Taxon


class IndividualQuerySet(models.QuerySet):
    def _filter_in_result(self, fieldname, value):
        result_type = self.model._get_default_identification_result_type()

        result_prefix = "identification_task__results__"
        return self.filter(**{result_prefix + "type": result_type, result_prefix + fieldname: value})

    def filter_by_taxon(self, taxon, include_descendants=False):
        if include_descendants:
            qs_kwargs = dict(fieldname="label__in", value=Taxon.get_tree(parent=taxon))
        else:
            qs_kwargs = dict(fieldname="label", value=taxon)

        return self._filter_in_result(**qs_kwargs)
