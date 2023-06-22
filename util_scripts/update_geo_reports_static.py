import django
from django.conf import settings
from django.db.models import F

import csv
import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

django.setup()

from tigapublic.models import MapAuxReports

ALL_REPORTS_FILENAME = "geo_all_complete_reports.csv"
SPECIES_ONLY_FILENAME = "geo_all_species_reports.csv"

# Common qs kwargs. Ensure only visible reports are used + all required fields are not null.
common_qs_filter_kwargs = dict(
    visible=True,
    observation_date__isnull=False,
    lon__isnull=False,
    lat__isnull=False
)

# Create common qs to be used.
common_qs = MapAuxReports.objects.filter(**common_qs_filter_kwargs).order_by("observation_date")

# Common model fields to be selected.
common_fields = ["observation_date", "lon", "lat"]

def qs_to_local_csv(qs, filename, path=settings.STATIC_ROOT, fields=None):
    if path is None:
        raise ValueError("path can not be empty.")
    if filename is None:
        raise ValueError("filename can not be empty.")
    filepath = os.path.join(path, filename)
    fields = fields or [x.name for x in qs.model._meta.get_fields()]
    dataset = list(qs.values(*fields).all())
    rows_done = 0
    with open(filepath, 'w') as my_file:
        writer = csv.DictWriter(my_file, fieldnames=fields)
        writer.writeheader()
        for data_item in dataset:
            writer.writerow(data_item)
            rows_done += 1
    print("{} rows completed".format(rows_done))


if __name__ == "__main__":

    # Update the geo reports files
    qs_to_local_csv(
        qs=common_qs,
        filename=ALL_REPORTS_FILENAME,
        fields=common_fields + ["type",],
    )

    # Update the geo species files 
    # QuerySet: filter by type=adult, expert_validate=True. Exclude those
    #           with validation_results starts with no (nosesabe, noseparece).
    qs_to_local_csv(
        qs=common_qs.filter(
            type='adult',
            expert_validated=True
        ).exclude(
            simplified_expert_validation_result__istartswith="no"
        ).annotate(
            # Rename validation result field to 'species'
            species=F('simplified_expert_validation_result')
        ),
        filename=SPECIES_ONLY_FILENAME,
        fields=common_fields + ["species",],
    )

