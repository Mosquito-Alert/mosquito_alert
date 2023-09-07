from django.db import models


class IndividualQuerySet(models.QuerySet):
    def _filter_in_result(self, fieldname, value):
        result_type = self.model._get_default_identification_result_type()

        result_prefix = "identification_task__results__"
        return self.filter(**{result_prefix + "type": result_type, result_prefix + fieldname: value})

    def filter_by_taxon(self, taxon):
        return self._filter_in_result(fieldname="label", value=taxon)
