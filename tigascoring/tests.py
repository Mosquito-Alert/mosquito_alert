from django.test import TestCase
from tigaserver_app.models import EuropeCountry, TigaUser, Report, ExpertReportAnnotation, Award, AwardCategory
from tigaserver_project import settings as conf
from django.utils import timezone
from datetime import datetime, timedelta, date
import pytz
from random import seed, random


class ScoringTestCase(TestCase):
    fixtures = ['awardcategory.json', 'tigausers.json', 'europe_countries.json', 'granter_user.json']

    def create_single_report(self, day, month, year, user, id, hour=None, minute=None, second=None):
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
        )
        return r

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
        day_1 = 1
        day_2 = 2 # --> 2 streak
        day_3 = 3 # --> 3 streak
        day_4 = 4
        day_5 = 5 # --> 2 streak
        day_6 = 6 # --> 3 streak
        day_7 = 7
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
