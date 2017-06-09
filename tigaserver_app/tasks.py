from __future__ import absolute_import

from celery import shared_task
from celery.task.schedules import crontab
from celery.decorators import periodic_task
from celery.utils.log import get_task_logger
from tigaserver_app.views import refresh_user_scores

@periodic_task(run_every=(crontab(minute='*/1')),name="refresh_user_scores_task",ignore_result=True)
def refresh_user_scores_task():
    refresh_user_scores()

