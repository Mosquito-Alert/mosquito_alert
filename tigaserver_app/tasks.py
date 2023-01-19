from __future__ import absolute_import

from celery.task.schedules import crontab
from celery.decorators import periodic_task
from tigaserver_app.views import refresh_user_scores
import tigaserver_project.settings as conf

@periodic_task(
    run_every=(crontab(minute=conf.CELERY_REFRESH_SCORE_FREQUENCY)),
    name="refresh_user_scores_task",
    ignore_result=True)
def refresh_user_scores_task():
    refresh_user_scores()

