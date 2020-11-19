from django.test import TestCase
from tigaserver_app.models import EuropeCountry, TigaUser, Report, ExpertReportAnnotation, Award, AwardCategory, \
    Notification, NotificationContent, get_translation_in, ACHIEVEMENT_10_REPORTS, ACHIEVEMENT_10_REPORTS_XP, \
    ACHIEVEMENT_20_REPORTS, ACHIEVEMENT_20_REPORTS_XP, ACHIEVEMENT_50_REPORTS, ACHIEVEMENT_50_REPORTS_XP
from tigaserver_project import settings as conf
from tigascoring.xp_scoring import compute_user_score_in_xp_v2
from django.utils import timezone
from datetime import datetime, timedelta, date
import pytz
from random import seed, random
from django.template.loader import render_to_string
import html.entities


class ScoringTestCase(TestCase):
    fixtures = ['awardcategory.json', 'tigausers.json', 'europe_countries.json', 'granter_user.json']

    def create_single_report(self, day, month, year, user, id, hour=None, minute=None, second=None, report_app_language='es'):
        utc = pytz.UTC
        if hour is None:
            hour = 0
        if minute is None:
            minute = 0
        if second is None:
            second = 0
        d = datetime(year, month, day, hour, minute, second)
        ld = utc.localize(d)
        seed(1)
        value_x = random()
        value_y = random()
        long = -180 + (value_x * (360))
        lat = -90 + (value_y * (180))
        r = Report(
            version_UUID=id,
            version_number=0,
            user_id=user.user_UUID,
            phone_upload_time=ld,
            server_upload_time=ld,
            creation_time=ld,
            version_time=ld,
            location_choice="current",
            current_location_lon=long,
            current_location_lat=lat,
            type='adult',
            app_language=report_app_language,
            package_version=32
        )
        return r

    def test_compute_score_for_new_user(self):
        user_id = '00000000-0000-0000-0000-000000000000'
        retval = compute_user_score_in_xp_v2(user_id)
        self.assertEqual(retval['total_score'], 0)

    def test_first_of_season_awarded(self):
        user_id = '00000000-0000-0000-0000-000000000000'
        day_before_start_of_season = conf.SEASON_START_DAY - 1
        month_before_start_of_season = conf.SEASON_START_MONTH - 1
        user = TigaUser.objects.get(pk=user_id)

        #should not be granted
        report_before_season = self.create_single_report(day_before_start_of_season, month_before_start_of_season, 2018, user, '00000000-0000-0000-0000-000000000001')
        report_before_season.save()
        self.assertEqual(Award.objects.filter(category__id=1).filter(given_to__user_UUID=user_id).count(), 0)

        # should be granted for season 2020
        report_in_season = self.create_single_report(conf.SEASON_START_DAY, conf.SEASON_START_MONTH, 2020, user, '00000000-0000-0000-0000-000000000002')
        report_in_season.save()
        self.assertEqual(Award.objects.filter(category__id=1).filter(given_to__user_UUID=user_id).filter(report__creation_time__year=2020).count(), 1)

        # should be granted for season 2018
        report_in_other_season = self.create_single_report(conf.SEASON_START_DAY, conf.SEASON_START_MONTH, 2018, user, '00000000-0000-0000-0000-000000000003')
        report_in_other_season.report_id = 'AAAA'
        report_in_other_season.save()
        self.assertEqual(Award.objects.filter(category__id=1).filter(given_to__user_UUID=user_id).filter(report__creation_time__year=2018).count(), 1)

        report_in_other_season_version = Report(
            version_UUID='00000000-0000-0000-0000-000000000004',
            version_number=1,
            report_id=report_in_other_season.report_id,
            user_id=report_in_other_season.user.user_UUID,
            phone_upload_time=report_in_other_season.phone_upload_time,
            server_upload_time=report_in_other_season.server_upload_time,
            creation_time=report_in_other_season.creation_time,
            version_time=report_in_other_season.version_time,
            location_choice="current",
            current_location_lon=report_in_other_season.lon,
            current_location_lat=report_in_other_season.lat,
            type='adult',
        )
        report_in_other_season_version.save()
        #award should be transferred to report_in_other_season_version
        self.assertEqual(Award.objects.filter(category__id=1).filter(given_to__user_UUID=user_id).filter(report__creation_time__year=2018).count(), 1)
        self.assertEqual(Award.objects.filter(category__id=1).filter(report=report_in_other_season_version).count(),1)
        self.assertEqual(Award.objects.filter(category__id=1).filter(report=report_in_other_season).count(), 0)

        report_in_other_season_version_2 = Report(
            version_UUID='00000000-0000-0000-0000-000000000005',
            version_number=2,
            report_id=report_in_other_season_version.report_id,
            user_id=report_in_other_season_version.user.user_UUID,
            phone_upload_time=report_in_other_season_version.phone_upload_time,
            server_upload_time=report_in_other_season_version.server_upload_time,
            creation_time=report_in_other_season_version.creation_time,
            version_time=report_in_other_season_version.version_time,
            location_choice="current",
            current_location_lon=report_in_other_season_version.lon,
            current_location_lat=report_in_other_season_version.lat,
            type='adult',
        )
        report_in_other_season_version_2.save()
        self.assertEqual(Award.objects.filter(category__id=1).filter(given_to__user_UUID=user_id).filter(report__creation_time__year=2018).count(), 1)
        self.assertEqual(Award.objects.filter(category__id=1).filter(report=report_in_other_season_version_2).count(), 1)
        self.assertEqual(Award.objects.filter(category__id=1).filter(report=report_in_other_season_version).count(), 0)

    def test_first_of_day(self):
        user_id = '00000000-0000-0000-0000-000000000000'
        user = TigaUser.objects.get(pk=user_id)
        day = 1
        month = 1
        year = 2015
        hour_1 = 1
        hour_2 = 2
        hour_3 = 3
        first_report_of_day = self.create_single_report(day, month, year, user, '00000000-0000-0000-0000-000000000001', hour_1)
        first_report_of_day.save()
        second_report_of_day = self.create_single_report(day, month, year, user, '00000000-0000-0000-0000-000000000002', hour_2)
        second_report_of_day.save()
        third_report_of_day = self.create_single_report(day, month, year, user, '00000000-0000-0000-0000-000000000003', hour_3)
        third_report_of_day.save()
        #just one first of day was granted
        self.assertEqual(Award.objects.filter(category__id=2).count(), 1)
        #it was granted to first_report_of_day
        self.assertEqual(Award.objects.get(category__id=2).report.version_UUID, first_report_of_day.version_UUID)

    def test_two_day_streak(self):
        user_id = '00000000-0000-0000-0000-000000000000'
        user = TigaUser.objects.get(pk=user_id)
        day_1 = 1
        day_2 = 2
        day_3 = 3
        month = 1
        year = 2015
        report_of_day_1 = self.create_single_report(day_1, month, year, user, '00000000-0000-0000-0000-000000000001')
        report_of_day_1.save()
        report_of_day_2 = self.create_single_report(day_2, month, year, user, '00000000-0000-0000-0000-000000000002')
        report_of_day_2.save()
        report_of_day_3 = self.create_single_report(day_3, month, year, user, '00000000-0000-0000-0000-000000000003')
        report_of_day_3.save()
        self.assertEqual(Award.objects.filter(category__id=3).count(), 1)

    def three_day_streak(self):
        user_id = '00000000-0000-0000-0000-000000000000'
        user = TigaUser.objects.get(pk=user_id)
        day_1 = 1
        day_2 = 2
        day_3 = 3 # --> 3 streak
        day_4 = 4
        month = 1
        year = 2015
        report_of_day_1 = self.create_single_report(day_1, month, year, user, '00000000-0000-0000-0000-000000000001')
        report_of_day_1.save()
        report_of_day_2 = self.create_single_report(day_2, month, year, user, '00000000-0000-0000-0000-000000000002')
        report_of_day_2.save()
        report_of_day_3 = self.create_single_report(day_3, month, year, user, '00000000-0000-0000-0000-000000000003')
        report_of_day_3.save()
        report_of_day_4 = self.create_single_report(day_4, month, year, user, '00000000-0000-0000-0000-000000000004')
        report_of_day_4.save()
        self.assertEqual(Award.objects.filter(category__id=4).count(), 1)
        self.assertEqual(Award.objects.get(category__id=4).report.version_UUID, report_of_day_3.version_UUID)

    def test_three_and_two_combined(self):
        user_id = '00000000-0000-0000-0000-000000000000'
        user = TigaUser.objects.get(pk=user_id)
        #All days are in the same week
        day_1 = 5
        day_2 = 6 # --> 2 streak
        day_3 = 7 # --> 3 streak
        day_4 = 8
        day_5 = 9 # --> 2 streak
        day_6 = 10 # --> 3 streak
        day_7 = 11
        month = 1
        year = 2015
        report_of_day_1 = self.create_single_report(day_1, month, year, user, '00000000-0000-0000-0000-000000000001')
        report_of_day_1.save()

        report_of_day_2 = self.create_single_report(day_2, month, year, user, '00000000-0000-0000-0000-000000000002')
        report_of_day_2.save()

        report_of_day_3 = self.create_single_report(day_3, month, year, user, '00000000-0000-0000-0000-000000000003')
        report_of_day_3.save()

        report_of_day_4 = self.create_single_report(day_4, month, year, user, '00000000-0000-0000-0000-000000000004')
        report_of_day_4.save()

        report_of_day_5 = self.create_single_report(day_5, month, year, user, '00000000-0000-0000-0000-000000000005')
        report_of_day_5.save()

        report_of_day_6 = self.create_single_report(day_6, month, year, user, '00000000-0000-0000-0000-000000000006')
        report_of_day_6.save()

        report_of_day_7 = self.create_single_report(day_7, month, year, user, '00000000-0000-0000-0000-000000000007')
        report_of_day_7.save()

        self.assertEqual(Award.objects.filter(category__id=4).count(), 2)
        self.assertEqual(Award.objects.filter(category__id=4).filter(report__version_UUID=report_of_day_3.version_UUID).count(), 1)
        self.assertEqual(Award.objects.filter(category__id=4).filter(report__version_UUID=report_of_day_6.version_UUID).count(), 1)
        self.assertEqual(Award.objects.filter(category__id=3).count(), 2)
        self.assertEqual(Award.objects.filter(category__id=3).filter(report__version_UUID=report_of_day_2.version_UUID).count(), 1)
        self.assertEqual(Award.objects.filter(category__id=3).filter(report__version_UUID=report_of_day_5.version_UUID).count(), 1)

    def test_corner_cases_daily_participation_midnight(self):
        user_id = '00000000-0000-0000-0000-000000000000'
        user = TigaUser.objects.get(pk=user_id)

        day_1 = 5  # --> Daily participation
        day_2 = 6  # --> Daily participation, 2 streak
        month = 1
        hour_1 = 23
        hour_2 = 0
        year = 2015

        report_of_day_1 = self.create_single_report(day_1, month, year, user, '00000000-0000-0000-0000-000000000001', hour_1)
        report_of_day_1.save()

        report_of_day_2 = self.create_single_report(day_2, month, year, user, '00000000-0000-0000-0000-000000000002', hour_2)
        report_of_day_2.save()

        self.assertEqual(Award.objects.filter(category__id=2).count(), 2) #Daily participation given to each of the reports
        self.assertEqual(Award.objects.filter(category__id=3).count(), 1)  #Two day streak given to one of the reports
        self.assertEqual(Award.objects.filter(category__id=2).filter(report__version_UUID=report_of_day_1.version_UUID).count(), 1) #Check each of the reports has first day
        self.assertEqual(Award.objects.filter(category__id=2).filter(report__version_UUID=report_of_day_2.version_UUID).count(), 1)
        self.assertEqual(Award.objects.filter(category__id=3).filter(report__version_UUID=report_of_day_2.version_UUID).count(), 1) #Check second report has 2 day streak

    def test_corner_cases_daily_participation_different_months(self):
        user_id = '00000000-0000-0000-0000-000000000000'
        user = TigaUser.objects.get(pk=user_id)

        day_1 = 30  # --> Daily participation
        day_2 = 1  # --> Daily participation, 2 streak
        month_1 = 4
        month_2 = 5
        year = 2020

        report_of_day_1 = self.create_single_report(day_1, month_1, year, user, '00000000-0000-0000-0000-000000000001')
        report_of_day_1.save()

        report_of_day_2 = self.create_single_report(day_2, month_2, year, user, '00000000-0000-0000-0000-000000000002')
        report_of_day_2.save()

        self.assertEqual(Award.objects.filter(category__id=2).count(),2)  # Daily participation given to each of the reports
        self.assertEqual(Award.objects.filter(category__id=3).count(), 1)  # Two day streak given to one of the reports
        self.assertEqual(Award.objects.filter(category__id=2).filter(report__version_UUID=report_of_day_1.version_UUID).count(),1)  # Check each of the reports has first day
        self.assertEqual(Award.objects.filter(category__id=2).filter(report__version_UUID=report_of_day_2.version_UUID).count(), 1)
        self.assertEqual(Award.objects.filter(category__id=3).filter(report__version_UUID=report_of_day_2.version_UUID).count(),1)  # Check second report has 2 day streak

    @staticmethod
    def get_notification_body_es(category_label, xp):
        context_es = {}
        table = {k: '&{};'.format(v) for k, v in html.entities.codepoint2name.items()}
        context_es['amount_awarded'] = xp
        context_es['reason_awarded'] = get_translation_in(category_label, 'es').translate(table)
        return render_to_string('tigaserver_app/award_notification_es.html', context_es).replace('&amp;','&')

    @staticmethod
    def get_notification_body_for_locale(category_label, xp, locale):
        context = {}
        table = {k: '&{};'.format(v) for k, v in html.entities.codepoint2name.items()}
        context['amount_awarded'] = xp
        context['reason_awarded'] = get_translation_in(category_label, locale).translate(table)
        return render_to_string('tigaserver_app/award_notification_' + locale + '.html', context).replace('&amp;','&')

    def test_10_day_achievement(self):
        user_id = '00000000-0000-0000-0000-000000000000'
        user = TigaUser.objects.get(pk=user_id)

        month_1 = 1
        year = 2020

        for i in range(1,11,1):
            r = self.create_single_report(i, month_1, year, user, '00000000-0000-0000-0000-0000000000' + str(i))
            r.save()
        self.assertEqual(Award.objects.filter(special_award_text='achievement_10_reports').count(), 1)  # Ten report achievement granted
        # emulate notifications
        if conf.DISABLE_ACHIEVEMENT_NOTIFICATIONS == False:
            notification_body = self.get_notification_body_es(ACHIEVEMENT_10_REPORTS, ACHIEVEMENT_10_REPORTS_XP)
            self.assertEqual(Notification.objects.filter(notification_content__body_html_es=notification_body).count(), 1)

    def test_20_day_achievement(self):
        user_id = '00000000-0000-0000-0000-000000000000'
        user = TigaUser.objects.get(pk=user_id)

        month_1 = 1
        year = 2020

        for i in range(1,21,1):
            r = self.create_single_report(i, month_1, year, user, '00000000-0000-0000-0000-0000000000' + str(i))
            r.save()
        self.assertEqual(Award.objects.filter(special_award_text='achievement_10_reports').count(), 1)  # Ten report achievement granted
        self.assertEqual(Award.objects.filter(special_award_text='achievement_20_reports').count(), 1)  # Ten report achievement granted

        # emulate notifications
        if conf.DISABLE_ACHIEVEMENT_NOTIFICATIONS == False:
            notification_body_10 = self.get_notification_body_es(ACHIEVEMENT_10_REPORTS, ACHIEVEMENT_10_REPORTS_XP)
            notification_body_20 = self.get_notification_body_es(ACHIEVEMENT_20_REPORTS, ACHIEVEMENT_20_REPORTS_XP)
            self.assertEqual(Notification.objects.filter(notification_content__body_html_es=notification_body_10).count(), 1)
            self.assertEqual(Notification.objects.filter(notification_content__body_html_es=notification_body_20).count(), 1)

    def test_50_day_achievement(self):
        user_id = '00000000-0000-0000-0000-000000000000'
        user = TigaUser.objects.get(pk=user_id)

        year = 2020

        for i in range(1, 3, 1):
            for j in range(1, 27 , 1):
                r = self.create_single_report(j, i, year, user, '00000000-0000-0000-0000-000000000' + str(j) + str(i))
                r.save()
        self.assertEqual(Award.objects.filter(special_award_text='achievement_10_reports').count(), 1)  # Ten report achievement granted
        self.assertEqual(Award.objects.filter(special_award_text='achievement_20_reports').count(), 1)  # Ten report achievement granted
        self.assertEqual(Award.objects.filter(special_award_text='achievement_50_reports').count(), 1)  # Ten report achievement granted

        # emulate notifications
        if conf.DISABLE_ACHIEVEMENT_NOTIFICATIONS == False:
            notification_body_10 = self.get_notification_body_es(ACHIEVEMENT_10_REPORTS, ACHIEVEMENT_10_REPORTS_XP)
            notification_body_20 = self.get_notification_body_es(ACHIEVEMENT_20_REPORTS, ACHIEVEMENT_20_REPORTS_XP)
            notification_body_50 = self.get_notification_body_es(ACHIEVEMENT_50_REPORTS, ACHIEVEMENT_50_REPORTS_XP)
            self.assertEqual(Notification.objects.filter(notification_content__body_html_es=notification_body_10).count(), 1)
            self.assertEqual(Notification.objects.filter(notification_content__body_html_es=notification_body_20).count(), 1)
            self.assertEqual(Notification.objects.filter(notification_content__body_html_es=notification_body_50).count(), 1)


    def test_corner_cases_first_of_season_different_users(self):
        user_id_1 = '00000000-0000-0000-0000-000000000000'
        user_id_2 = '00000000-0000-0000-0000-000000000001'

        day_1 = 30  # --> Daily participation, first of season
        month_1 = 4
        year = 2020

        user_1 = TigaUser.objects.get(pk=user_id_1)
        user_2 = TigaUser.objects.get(pk=user_id_2)

        report_1_user_1 = self.create_single_report(day_1, month_1, year, user_1, '00000000-0000-0000-0000-000000000001')
        report_1_user_1.save()
        report_1_user_2 = self.create_single_report(day_1, month_1, year, user_2, '00000000-0000-0000-0000-000000000002')
        report_1_user_2.save()

        self.assertEqual(Award.objects.filter(category__id=1).count(),2)  # Daily participation given to each of the reports
        self.assertEqual(Award.objects.filter(category__id=1).count(),2)  # First of season given to each of the reports
        self.assertEqual(Award.objects.filter(category__id=1).filter(report__version_UUID=report_1_user_1.version_UUID).count(), 1)
        self.assertEqual(Award.objects.filter(category__id=1).filter(report__version_UUID=report_1_user_2.version_UUID).count(), 1)


    def test_10_day_achievement_for_sq_locale(self):
        user_id = '00000000-0000-0000-0000-000000000000'
        user = TigaUser.objects.get(pk=user_id)

        month_1 = 1
        year = 2020

        for i in range(1,11,1):
            r = self.create_single_report(i, month_1, year, user, '00000000-0000-0000-0000-0000000000' + str(i), report_app_language='sq')
            r.save()
        self.assertEqual(Award.objects.filter(special_award_text='achievement_10_reports').count(), 1)  # Ten report achievement granted
        # emulate notifications
        if conf.DISABLE_ACHIEVEMENT_NOTIFICATIONS == False:
            notification_body = self.get_notification_body_for_locale(ACHIEVEMENT_10_REPORTS, ACHIEVEMENT_10_REPORTS_XP,'sq')
            #The english notification should be in Albanian
            self.assertEqual(Notification.objects.filter(notification_content__body_html_en=notification_body).count(), 1)

    def test_10_day_achievement_for_el_locale(self):
        user_id = '00000000-0000-0000-0000-000000000000'
        user = TigaUser.objects.get(pk=user_id)

        month_1 = 1
        year = 2020

        for i in range(1,11,1):
            r = self.create_single_report(i, month_1, year, user, '00000000-0000-0000-0000-0000000000' + str(i), report_app_language='el')
            r.save()
        self.assertEqual(Award.objects.filter(special_award_text='achievement_10_reports').count(), 1)  # Ten report achievement granted
        # emulate notifications
        if conf.DISABLE_ACHIEVEMENT_NOTIFICATIONS == False:
            notification_body = self.get_notification_body_for_locale(ACHIEVEMENT_10_REPORTS, ACHIEVEMENT_10_REPORTS_XP,'el')
            print(notification_body)
            #The english notification should be in Albanian
            self.assertEqual(Notification.objects.filter(notification_content__body_html_en=notification_body).count(), 1)
