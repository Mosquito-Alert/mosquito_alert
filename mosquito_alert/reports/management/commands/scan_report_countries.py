from tqdm import tqdm

from django.core.management.base import BaseCommand
from django.utils import timezone

from mosquito_alert.reports.models import Report


class Command(BaseCommand):
    help = "Scan reports and update their countries"

    def handle(self, *args, **options):
        # Re-scan reports for country
        reports_to_update = []
        report_without_country_qs = Report.objects.filter(country__isnull=True)
        with tqdm(total=report_without_country_qs.count()) as progress_bar:
            for r in report_without_country_qs.iterator():
                if country := r._get_country_is_in():
                    r.country = country
                    r.updated_at = timezone.now()
                    reports_to_update.append(r)
                _ = progress_bar.update()

        if reports_to_update:
            Report.objects.bulk_update(
                objs=reports_to_update,
                fields=["country", "updated_at"],
                batch_size=2000,
            )
