from django.core.management.base import BaseCommand
from multiprocessing import Pool
import os
from tqdm import tqdm

from tigacrafting.models import IdentificationTask

def refresh_task(task_data):
    from django import db
    db.connections.close_all()
    task, force = task_data
    try:
        task.refresh(force=force, commit=True)
    except Exception as e:
        print(task.pk, e)

class Command(BaseCommand):
    help = 'Refresh identification tasks'

    def add_arguments(self, parser):
        # Add --force as an optional argument
        parser.add_argument(
            '--force',
            action='store_true',
            help='Force refresh (use force=True)',
        )

        parser.add_argument(
            '--multiprocessing',
            action='store_true',
            help='Use multiprocessing for refreshing tasks',
        )

    def handle(self, *args, **options):
        identification_tasks_qs = IdentificationTask.objects.all().select_related('report', 'taxon')

        if options['multiprocessing']:
            # Prepare task data (task and force option) to pass to worker pool
            tasks_data = ((task, options['force']) for task in identification_tasks_qs.iterator())

            # Calculate 80% of the total processors, but ensure it's at least 1
            num_processors = max(1, int(os.cpu_count() * 0.8))

            # Create a Pool with the calculated number of processes
            with Pool(processes=num_processors) as pool:
                # Use tqdm to show progress bar with pool.imap
                list(tqdm(pool.imap_unordered(refresh_task, tasks_data, chunksize=100), total=identification_tasks_qs.count()))
        else:
            # If multiprocessing is not enabled, handle tasks without it
            for task in tqdm(identification_tasks_qs.iterator(), total=identification_tasks_qs.count()):
                try:
                    task.refresh(force=options['force'], commit=True)
                except Exception as e:
                    print(task.pk, e)
