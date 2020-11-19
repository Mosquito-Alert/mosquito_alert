'''
Retroactively assign first report of season, first report of day, two day consecutive participation and three day consecutive participation
'''
import os, sys

proj_path = "/home/webuser/webapps/tigaserver/"
os.environ.setdefault("DJANGO_SETTINGS_MODULE", "tigaserver_project.settings")
sys.path.append(proj_path)

os.chdir(proj_path + "util_scripts/")

from django.core.wsgi import get_wsgi_application

application = get_wsgi_application()

from tigaserver_app.models import grant_first_of_day, grant_first_of_season, grant_three_consecutive_days_sending, \
    grant_two_consecutive_days_sending, Award, grant_10_reports_achievement, grant_20_reports_achievement, \
    grant_50_reports_achievement
from tigaserver_app.models import Report, TigaUser, TigaProfile
from django.contrib.auth.models import User
import tigaserver_project.settings as conf
from datetime import datetime, timedelta, date
import pytz


def get_uuid_replicas():
    profiles = TigaProfile.objects.all()
    exclude = []
    for p in profiles:
        if p.profile_devices.count() > 1:
            i = 0
            for d in p.profile_devices.all().order_by('user_UUID'):
                if i > 0:
                    exclude.append(d.user_UUID)
                i+=1
    return exclude

def daterange(start_date, end_date):
    for n in range(int ((end_date - start_date).days)):
        yield start_date + timedelta(n)

def init_date_struct(start_date, end_date):
    date_struct = {}
    for single_date in daterange(start_date, end_date):
        week = single_date.isocalendar()[1]
        year = single_date.year
        try:
            date_struct[str(year)]
        except KeyError:
            date_struct[str(year)] = {}

        try:
            date_struct[str(year)][str(week)]
        except KeyError:
            date_struct[str(year)][str(week)] = {}

        try:
            current_ini = date_struct[str(year)][str(week)]['ini']
            if single_date < current_ini:
                date_struct[str(year)][str(week)]['ini'] = single_date
        except KeyError:
            date_struct[str(year)][str(week)]['ini'] = single_date

        try:
            current_end = date_struct[str(year)][str(week)]['end']
            if single_date >= current_end:
                date_struct[str(year)][str(week)]['end'] = single_date
        except KeyError:
            date_struct[str(year)][str(week)]['end'] = single_date

    return date_struct


def one_day_between_and_same_week(r1_date_less_recent, r2_date_most_recent):
    day_before = r2_date_most_recent - timedelta(days=1)
    week_less_recent = r1_date_less_recent.isocalendar()[1]
    week_most_recent = r2_date_most_recent.isocalendar()[1]
    return day_before.year == r1_date_less_recent.year and day_before.month == r1_date_less_recent.month and day_before.day == r1_date_less_recent.day and week_less_recent == week_most_recent


def same_day(r1_date_less_recent, r2_date_most_recent):
    return r1_date_less_recent.year == r2_date_most_recent.year and r1_date_less_recent.month == r2_date_most_recent.month and r1_date_less_recent.day == r2_date_most_recent.day


def can_be_first_of_season( report, year ):
    utc = pytz.UTC
    #naive datetime
    d = datetime(year, conf.SEASON_START_MONTH, conf.SEASON_START_DAY)
    #localized datetime
    ld = utc.localize(d)
    return report.creation_time >= ld


def get_all_user_reports(user):
    user_uuids = []
    if user.profile:
        ps = user.profile.profile_devices.all()
        for p in ps:
            user_uuids.append(p.user_UUID)
    else:
        user_uuids.append(user.user_UUID)
    return Report.objects.filter(user__user_UUID__in=user_uuids).exclude(type='bite')


def give_retroactive_awards_to_user(user, granter):
    print("Starting new user")
    user_reports = get_all_user_reports(user).order_by('creation_time')
    first_of_season_awarded_for_year = []
    last_versions = list(filter(lambda x: not x.deleted and x.latest_version, user_reports))
    if len(last_versions) > 0:
        if len(last_versions) > 1:
            two_consecutives = False
            last_awarded_was_three = False
            last_report = None
            current_day = None
            report_counter = 0
            for report in last_versions:
                report_counter += 1
                if report_counter == 10:
                    grant_10_reports_achievement(report, granter)
                if report_counter == 20:
                    grant_20_reports_achievement(report, granter)
                if report_counter == 50:
                    grant_50_reports_achievement(report, granter)

                if not report.creation_time.year in first_of_season_awarded_for_year:
                    if can_be_first_of_season(report, report.creation_time.year):
                        # Award first of season
                        print("Awarded first of season to {0} for year {1}".format(report.creation_time,
                                                                                   report.creation_time.year))
                        grant_first_of_season(report, granter)
                        first_of_season_awarded_for_year.append(report.creation_time.year)

                if current_day is None:
                    # is first of day
                    print("Awarded first of day for report {0}".format(report.creation_time))
                    grant_first_of_day(report, granter)
                else:
                    if not same_day(current_day, report.creation_time):
                        print("Awarded first of day for report {0}".format(report.creation_time))
                        grant_first_of_day(report, granter)

                if last_report:
                    if one_day_between_and_same_week(last_report.creation_time,
                                                     report.creation_time) and last_awarded_was_three == False:
                        if two_consecutives == True:
                            print("Three consecutive reports {0} {1}".format(last_report.creation_time,
                                                                             report.creation_time))
                            grant_three_consecutive_days_sending(report, granter)
                            last_awarded_was_three = True
                            two_consecutives = False
                        else:
                            print("Two consecutive reports {0} {1}".format(last_report.creation_time,
                                                                           report.creation_time))
                            grant_two_consecutive_days_sending(report, granter)
                            last_awarded_was_three = False
                            two_consecutives = True
                    else:
                        print("Non consecutive reports {0} {1}".format(last_report.creation_time, report.creation_time))
                        if not same_day(last_report.creation_time, report.creation_time):
                            last_awarded_was_three = False
                            two_consecutives = False
                last_report = report
                current_day = date(report.creation_time.year, report.creation_time.month, report.creation_time.day)
        else:
            print("Awarded first of season to {0} for year {1}".format(last_versions[0].creation_time,
                                                                       last_versions[0].creation_time.year))
            grant_first_of_season(last_versions[0], granter)
            grant_first_of_day(last_versions[0], granter)
        # print("User {0} - {1} n reports, date_ini {2} date_end {3}".format( user.user_UUID, len(last_versions), date_ini, date_end))


def test_awards_for_grandmaster():
    u = TigaUser.objects.get(pk='7f913feb-715c-4d46-ab8f-617678b56406')
    granter = User.objects.get(pk=24)  # super_movelab
    give_retroactive_awards_to_user(u, granter)

def crunch():
    #cleanup
    Award.objects.all().delete()
    uuid_replicas = get_uuid_replicas()
    users = TigaUser.objects.exclude(score_v2=0).exclude(user_UUID__in=uuid_replicas)
    granter = User.objects.get(pk=24) #super_movelab

    for user in users:
        give_retroactive_awards_to_user( user, granter )



#test_awards_for_grandmaster()
crunch()


#{ '2004':{ '1':[], '2':[] }, '2005':{ '1': [], '2':[] } }