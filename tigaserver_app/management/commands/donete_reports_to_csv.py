import csv
from datetime import datetime
from operator import itemgetter

from django.core.management.base import BaseCommand
from django.utils import timezone

from tigaserver_app.models import Report

FROM_DATETIME_UTC = datetime(year=2022, month=7, day=5, tzinfo=timezone.utc)
FROM_DATABASE = "donete"


def get_diff_objects_between_databases(model, filters=None, from_db=FROM_DATABASE):
    from_qs = model.objects.using(from_db)
    if filters:
        from_qs = from_qs.filter(**filters)
    ids_not_found = set(from_qs.values_list("pk", flat=True)) - set(
        model.objects.values_list("pk", flat=True)
    )
    return model.objects.using(from_db).filter(pk__in=ids_not_found)


class Command(BaseCommand):
    help = "Export queryset to CSV"

    def handle(self, *args, **options):
        reports_not_in_prod = get_diff_objects_between_databases(
            model=Report, filters=dict(server_upload_time__gte=FROM_DATETIME_UTC)
        ).order_by("server_upload_time")

        # Specify the file path where you want to save the CSV file
        file_path = "./reports_not_in_prod_20240110.csv"

        # Call the function to export the queryset to CSV
        self.export_to_csv(reports_not_in_prod, file_path)

        self.stdout.write(self.style.SUCCESS("Successfully exported data to CSV"))

    def export_to_csv(self, queryset, file_path):
        with open(file_path, "w", newline="") as csv_file:
            # Create a CSV writer
            csv_writer = csv.writer(csv_file)

            # Write the header row based on your model fields
            header = [field.column for field in Report._meta.local_fields]
            csv_writer.writerow(header)

            # Write data rows
            for obj in queryset.iterator():
                csv_writer.writerow(itemgetter(*header)(obj.__dict__))
