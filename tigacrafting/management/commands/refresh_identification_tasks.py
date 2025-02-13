from django.core.management.base import BaseCommand
from tqdm import tqdm

from tigacrafting.models import IdentificationTask

class Command(BaseCommand):
    def handle(self, *args, **options):
        identification_tasks_qs = IdentificationTask.objects.all().select_related('report')

        tasks_to_update = []
        for task in tqdm(identification_tasks_qs.iterator(), total=identification_tasks_qs.count()):
            task.refresh(commit=True)
            tasks_to_update.append(task)
