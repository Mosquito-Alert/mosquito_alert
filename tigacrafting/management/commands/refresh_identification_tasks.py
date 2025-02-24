from django.core.management.base import BaseCommand
from tqdm import tqdm

from tigacrafting.models import IdentificationTask

class Command(BaseCommand):
    help = 'Refresh identification tasks'

    def add_arguments(self, parser):
        # Add --force as an optional argument
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force refresh (use force=True)',
        )

    def handle(self, *args, **options):
        identification_tasks_qs = IdentificationTask.objects.all().select_related('report', 'taxon')

        for task in tqdm(identification_tasks_qs.iterator(), total=identification_tasks_qs.count()):
            try:
                task.refresh(force=options['force'], commit=True)
            except Exception as e:
                print(task.pk, e)
