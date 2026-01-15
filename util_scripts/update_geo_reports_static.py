import django
from django.conf import settings

import csv
import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

django.setup()

from tigacrafting.models import IdentificationTask
from tigaserver_app.models import Report

ALL_REPORTS_FILENAME = "geo_all_complete_reports.csv"
SPECIES_ONLY_FILENAME = "geo_all_species_reports.csv"


# Create common qs to be used.
common_qs = Report.objects.filter(point__isnull=False).published().non_deleted().order_by("creation_time")

def qs_to_local_csv(qs, filename, path=settings.STATIC_ROOT, fields=None):
    if path is None:
        raise ValueError("path can not be empty.")
    if filename is None:
        raise ValueError("filename can not be empty.")
    if not isinstance(fields, dict):
        raise ValueError("fields must be a dictionary mapping CSV column names to callables.")

    filepath = os.path.join(path, filename)

    rows_done = 0
    with open(filepath, 'w') as my_file:
        writer = csv.DictWriter(my_file, fieldnames=fields.keys())
        writer.writeheader()

        for data_item in qs.iterator(chunk_size=2000):
            writer.writerow({key: func(data_item) for key, func in fields.items()})
            rows_done += 1
    print("{} rows completed".format(rows_done))


if __name__ == "__main__":

    # Update the geo reports files
    qs_to_local_csv(
        qs=common_qs,
        filename=ALL_REPORTS_FILENAME,
        fields={
            'observation_date': lambda x: x.creation_time,
            'lon': lambda x: x.point.x,
            'lat': lambda x: x.point.y,
            'type': lambda x: x.type,
        }
    )

    # Update the geo species files 
    # QuerySet: filter by type=adult
    qs_to_local_csv(
        qs=common_qs.filter(
            type=Report.TYPE_ADULT,
            identification_task__isnull=False,
            identification_task__status=IdentificationTask.Status.DONE,
            identification_task__taxon__pk__in=[
                112, # albopictus
                113, # aegypti
                10, # culex
                114, # japonicus
                115, # koreicus
            ]
        ).select_related('identification_task__taxon'),
        filename=SPECIES_ONLY_FILENAME,
        fields={
            'observation_date': lambda x: x.creation_time,
            'lon': lambda x: x.point.x,
            'lat': lambda x: x.point.y,
            'species': lambda x: x.identification_task.taxon.name.lower().replace(" ", "_")
        },
    )

