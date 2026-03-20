
from datetime import timedelta

from django.db.models.signals import post_save
from django.dispatch import receiver
from django.conf import settings
from django.contrib.auth import get_user_model

from mosquito_alert.tigaserver_app.models import Report

from .models import Award
from .utils import (
    grant_first_of_season,
    grant_first_of_day,
    grant_two_consecutive_days_sending,
    grant_three_consecutive_days_sending,
    grant_10_reports_achievement,
    grant_20_reports_achievement,
    grant_50_reports_achievement,
    one_day_between_and_same_week
)

User = get_user_model()


@receiver(post_save, sender=Report)
def maybe_give_awards(sender, instance, created, **kwargs):
    #only for adults and sites
    if created:
        try:
            super_movelab = User.objects.get(pk=24)
            n_reports = Report.objects.filter(user=instance.user).exclude(type=Report.TYPE_BITE).non_deleted().count()
            if n_reports == 10:
                grant_10_reports_achievement(instance, super_movelab)
            if n_reports == 20:
                grant_20_reports_achievement(instance, super_movelab)
            if n_reports == 50:
                grant_50_reports_achievement(instance, super_movelab)
            if instance.type == Report.TYPE_ADULT or instance.type == Report.TYPE_SITE:
                # check award for first of season
                current_year = instance.creation_time.year
                awards = Award.objects.filter(given_to=instance.user).filter(report__creation_time__year=current_year).filter(category__category_label='start_of_season')
                if awards.count() == 0:  # not yet awarded
                    # can be first of season?
                    if instance.creation_time.month >= settings.SEASON_START_MONTH and instance.creation_time.day >= settings.SEASON_START_DAY:
                        grant_first_of_season(instance, super_movelab)

                report_day = instance.creation_time.day
                report_month = instance.creation_time.month
                report_year = instance.creation_time.year
                awards = Award.objects \
                    .filter(report__creation_time__year=report_year) \
                    .filter(report__creation_time__month=report_month) \
                    .filter(report__creation_time__day=report_day) \
                    .filter(report__user=instance.user) \
                    .filter(category__category_label='daily_participation').order_by(
                    'report__creation_time')  # first is oldest
                if awards.count() == 0: # not yet awarded
                    grant_first_of_day(instance, super_movelab)

                date_1_day_before_report = instance.creation_time - timedelta(days=1)
                date_1_day_before_report_adjusted = date_1_day_before_report.replace(hour=23, minute=59, second=59)
                report_before_this_one = Report.objects.filter(user=instance.user).filter(creation_time__lte=date_1_day_before_report_adjusted).order_by('-creation_time').first()  # first is most recent
                if report_before_this_one is not None and one_day_between_and_same_week(report_before_this_one.creation_time, instance.creation_time):
                    #report before this one has not been awarded neither 2nd nor 3rd day streak
                    if Award.objects.filter(report=report_before_this_one).filter(category__category_label='fidelity_day_2').count()==0 and Award.objects.filter(report=report_before_this_one).filter(category__category_label='fidelity_day_3').count()==0:
                        grant_two_consecutive_days_sending(instance, super_movelab)
                    else:
                        if Award.objects.filter(report=report_before_this_one).filter(category__category_label='fidelity_day_2').count() == 1:
                            grant_three_consecutive_days_sending(instance, super_movelab)
        except User.DoesNotExist:
            pass
