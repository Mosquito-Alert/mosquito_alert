from tqdm import tqdm

from django.core.management.base import BaseCommand
from django.utils import timezone

from mosquito_alert.reports.models import Report


class Command(BaseCommand):
    help = "Scan reports and update their countries"

    def handle(self, *args, **options):
        # Re-scan reports for country
        report_without_country_qs = Report.objects.filter(country__isnull=True)
        with tqdm(total=report_without_country_qs.count()) as progress_bar:
            for r in report_without_country_qs.iterator():
                if country := r._get_country_is_in():
                    Report.objects.filter(pk=r.pk).update(
                        country=country,
                        updated_at=timezone.now(),
                    )
                _ = progress_bar.update()
