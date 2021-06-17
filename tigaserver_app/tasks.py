from __future__ import absolute_import

from celery import shared_task
from celery.task.schedules import crontab
from celery.decorators import periodic_task
from celery.utils.log import get_task_logger
from tigaserver_app.views import refresh_user_scores
import tigaserver_project.settings as conf
from tigaserver_project.celery import app
from tigascoring.xp_scoring import compute_user_score_in_xp_v2


@periodic_task(
    run_every=(crontab(minute=conf.CELERY_REFRESH_SCORE_FREQUENCY)),
    name="refresh_user_scores_task",
    ignore_result=True)
def refresh_user_scores_task():
    refresh_user_scores()

@app.task
def async_compute_user_score_v2(user_id):
    compute_user_score_in_xp_v2(user_id, True)