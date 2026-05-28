from django.conf import settings
from django.test import TestCase
from django.utils.translation import activate, deactivate, gettext as _
from mosquito_alert.awards.models import Award
from mosquito_alert.awards.utils import (
    ACHIEVEMENT_10_REPORTS,
    ACHIEVEMENT_10_REPORTS_XP,
    ACHIEVEMENT_20_REPORTS,
    ACHIEVEMENT_20_REPORTS_XP,
    ACHIEVEMENT_50_REPORTS,
    ACHIEVEMENT_50_REPORTS_XP,
)
from mosquito_alert.taxa.models import Taxon
from mosquito_alert.identification_tasks.models import ExpertReportAnnotation
from mosquito_alert.identification_tasks.tests.factories import (
    ExpertReportAnnotationFactory,
)
from mosquito_alert.reports.models import Report
from mosquito_alert.reports.tests.factories import (
    ObservationReportFactory,
    ObservationReportWithoutSignalFactory,
)
from mosquito_alert.notifications.models import Notification
from mosquito_alert.awards.xp_scoring import compute_user_score_in_xp_v2
from mosquito_alert.users.tests.factories import TigaUserFactory
from datetime import datetime
from zoneinfo import ZoneInfo

from django.template.loader import render_to_string


class ScoringTestCase(TestCase):
    fixtures = [
        "awardcategory.json",
        "granter_user.json",
        "taxon.json",
    ]

    def test_compute_score_for_new_user(self):
        user = TigaUserFactory()
        retval = compute_user_score_in_xp_v2(user.pk)
        self.assertEqual(retval["total_score"], 0)

    def test_score_non_validated_adult_report(self):
        user = TigaUserFactory()

        # Report in season
        ObservationReportFactory(
            user=user,
            phone_upload_time=datetime(
                2020,
                settings.SEASON_START_MONTH,
                settings.SEASON_START_DAY,
                tzinfo=ZoneInfo("UTC"),
            ),
        )

        retval = compute_user_score_in_xp_v2(user.pk)
        # 6 points first of season
        # 6 points first of day
        # no awards for mosquito. not yet classified
        self.assertEqual(retval["total_score"], 12)

    def test_score_for_aedes_adult_report(self):
        user = TigaUserFactory()

        report_in_season = ObservationReportFactory(
            user=user,
            phone_upload_time=datetime(
                2020,
                settings.SEASON_START_MONTH,
                settings.SEASON_START_DAY,
                tzinfo=ZoneInfo("UTC"),
            ),
        )

        identification_task = report_in_season.identification_task

        report_in_season.refresh_from_db()
        aedes_albopictus = Taxon.objects.get(pk=112)
        _ = ExpertReportAnnotationFactory(
            identification_task=identification_task,
            taxon=aedes_albopictus,
            decision_level=ExpertReportAnnotation.DecisionLevel.FINAL,
            confidence=ExpertReportAnnotation.ConfidenceCategory.DEFINITELY,
        )
        retval = compute_user_score_in_xp_v2(user.pk)
        # 6 points first of season
        # 6 points first of day
        # 6 points geolocated
        # 6 points picture
        self.assertEqual(retval["total_score"], 24)
        # we hide the report, it does not yield any points
        report_in_season.hide = True
        report_in_season.save()
        retval = compute_user_score_in_xp_v2(user.pk)
        self.assertEqual(retval["total_score"], 0)

    def test_first_of_season_awarded(self):
        day_before_start_of_season = settings.SEASON_START_DAY - 1
        month_before_start_of_season = settings.SEASON_START_MONTH - 1
        user = TigaUserFactory()

        # should not be granted: report_before_season
        ObservationReportFactory(
            user=user,
            phone_upload_time=datetime(
                2018,
                month_before_start_of_season,
                day_before_start_of_season,
                tzinfo=ZoneInfo("UTC"),
            ),
        )

        self.assertEqual(
            Award.objects.filter(category__id=1).filter(given_to=user).count(),
            0,
        )

        # should be granted for season 2020
        ObservationReportFactory(
            user=user,
            phone_upload_time=datetime(
                2020,
                settings.SEASON_START_MONTH,
                settings.SEASON_START_DAY,
                tzinfo=ZoneInfo("UTC"),
            ),
        )

        self.assertEqual(
            Award.objects.filter(category__id=1)
            .filter(given_to=user)
            .filter(report__creation_time__year=2020)
            .count(),
            1,
        )

        # should be granted for season 2018
        report_in_other_season = ObservationReportFactory(
            user=user,
            phone_upload_time=datetime(
                2018,
                settings.SEASON_START_MONTH,
                settings.SEASON_START_DAY,
                tzinfo=ZoneInfo("UTC"),
            ),
        )

        self.assertEqual(
            Award.objects.filter(category__id=1)
            .filter(given_to=user)
            .filter(report__creation_time__year=2018)
            .count(),
            1,
        )

        # Creating a new version
        report_in_other_season.location_choice = Report.LOCATION_CURRENT
        report_in_other_season.type = Report.TYPE_ADULT
        report_in_other_season.save()

        # award should be kept
        self.assertEqual(
            Award.objects.filter(category__id=1)
            .filter(given_to=user)
            .filter(report__creation_time__year=2018)
            .count(),
            1,
        )
        self.assertEqual(
            Award.objects.filter(category__id=1)
            .filter(report=report_in_other_season)
            .count(),
            1,
        )

    def test_first_of_day(self):
        user = TigaUserFactory()
        day = 1
        month = 1
        year = 2015
        hour_1 = 1
        hour_2 = 2
        hour_3 = 3

        first_report_of_day = ObservationReportFactory(
            user=user,
            phone_upload_time=datetime(
                year, month, day, hour_1, tzinfo=ZoneInfo("UTC")
            ),
        )

        ObservationReportFactory(
            user=user,
            phone_upload_time=datetime(
                year, month, day, hour_2, tzinfo=ZoneInfo("UTC")
            ),
        )
        ObservationReportFactory(
            user=user,
            phone_upload_time=datetime(
                year, month, day, hour_3, tzinfo=ZoneInfo("UTC")
            ),
        )
        # just one first of day was granted
        self.assertEqual(Award.objects.filter(category__id=2).count(), 1)
        # it was granted to first_report_of_day
        self.assertEqual(
            Award.objects.get(category__id=2).report,
            first_report_of_day,
        )

    def test_two_day_streak(self):
        user = TigaUserFactory()
        day_1 = 1
        day_2 = 2
        day_3 = 3
        month = 1
        year = 2015

        ObservationReportFactory(
            user=user,
            phone_upload_time=datetime(year, month, day_1, tzinfo=ZoneInfo("UTC")),
        )

        ObservationReportFactory(
            user=user,
            phone_upload_time=datetime(year, month, day_2, tzinfo=ZoneInfo("UTC")),
        )

        ObservationReportFactory(
            user=user,
            phone_upload_time=datetime(year, month, day_3, tzinfo=ZoneInfo("UTC")),
        )

        self.assertEqual(Award.objects.filter(category__id=3).count(), 1)

    def test_three_day_streak(self):
        user = TigaUserFactory()
        day_1 = 1
        day_2 = 2
        day_3 = 3  # --> 3 streak
        day_4 = 4
        month = 1
        year = 2015

        ObservationReportFactory(
            user=user,
            phone_upload_time=datetime(year, month, day_1, tzinfo=ZoneInfo("UTC")),
        )

        ObservationReportFactory(
            user=user,
            phone_upload_time=datetime(year, month, day_2, tzinfo=ZoneInfo("UTC")),
        )
        report_of_day_3 = ObservationReportFactory(
            user=user,
            phone_upload_time=datetime(year, month, day_3, tzinfo=ZoneInfo("UTC")),
        )
        ObservationReportFactory(
            user=user,
            phone_upload_time=datetime(year, month, day_4, tzinfo=ZoneInfo("UTC")),
        )
        self.assertEqual(Award.objects.filter(category__id=4).count(), 1)
        self.assertEqual(
            Award.objects.get(category__id=4).report,
            report_of_day_3,
        )

    def test_three_and_two_combined(self):

        user = TigaUserFactory()
        # All days are in the same week
        day_1 = 5
        day_2 = 6  # --> 2 streak
        day_3 = 7  # --> 3 streak
        day_4 = 8
        day_5 = 9  # --> 2 streak
        day_6 = 10  # --> 3 streak
        day_7 = 11
        month = 1
        year = 2015
        ObservationReportFactory(
            user=user,
            phone_upload_time=datetime(year, month, day_1, tzinfo=ZoneInfo("UTC")),
        )

        report_of_day_2 = ObservationReportFactory(
            user=user,
            phone_upload_time=datetime(year, month, day_2, tzinfo=ZoneInfo("UTC")),
        )

        report_of_day_3 = ObservationReportFactory(
            user=user,
            phone_upload_time=datetime(year, month, day_3, tzinfo=ZoneInfo("UTC")),
        )

        ObservationReportFactory(
            user=user,
            phone_upload_time=datetime(year, month, day_4, tzinfo=ZoneInfo("UTC")),
        )

        report_of_day_5 = ObservationReportFactory(
            user=user,
            phone_upload_time=datetime(year, month, day_5, tzinfo=ZoneInfo("UTC")),
        )

        report_of_day_6 = ObservationReportFactory(
            user=user,
            phone_upload_time=datetime(year, month, day_6, tzinfo=ZoneInfo("UTC")),
        )

        ObservationReportFactory(
            user=user,
            phone_upload_time=datetime(year, month, day_7, tzinfo=ZoneInfo("UTC")),
        )

        self.assertEqual(Award.objects.filter(category__id=4).count(), 2)
        self.assertEqual(
            Award.objects.filter(category__id=4).filter(report=report_of_day_3).count(),
            1,
        )
        self.assertEqual(
            Award.objects.filter(category__id=4).filter(report=report_of_day_6).count(),
            1,
        )
        self.assertEqual(Award.objects.filter(category__id=3).count(), 2)
        self.assertEqual(
            Award.objects.filter(category__id=3).filter(report=report_of_day_2).count(),
            1,
        )
        self.assertEqual(
            Award.objects.filter(category__id=3).filter(report=report_of_day_5).count(),
            1,
        )

    def test_corner_cases_daily_participation_midnight(self):
        user = TigaUserFactory()

        day_1 = 5  # --> Daily participation
        day_2 = 6  # --> Daily participation, 2 streak
        month = 1
        hour_1 = 23
        hour_2 = 0
        year = 2015

        report_of_day_1 = ObservationReportFactory(
            user=user,
            phone_upload_time=datetime(
                year, month, day_1, hour_1, tzinfo=ZoneInfo("UTC")
            ),
        )

        report_of_day_2 = ObservationReportFactory(
            user=user,
            phone_upload_time=datetime(
                year, month, day_2, hour_2, tzinfo=ZoneInfo("UTC")
            ),
        )

        self.assertEqual(
            Award.objects.filter(category__id=2).count(), 2
        )  # Daily participation given to each of the reports
        self.assertEqual(
            Award.objects.filter(category__id=3).count(), 1
        )  # Two day streak given to one of the reports
        self.assertEqual(
            Award.objects.filter(category__id=2).filter(report=report_of_day_1).count(),
            1,
        )  # Check each of the reports has first day
        self.assertEqual(
            Award.objects.filter(category__id=2).filter(report=report_of_day_2).count(),
            1,
        )
        self.assertEqual(
            Award.objects.filter(category__id=3).filter(report=report_of_day_2).count(),
            1,
        )  # Check second report has 2 day streak

    def test_corner_cases_daily_participation_different_months(self):
        user = TigaUserFactory()

        day_1 = 30  # --> Daily participation
        day_2 = 1  # --> Daily participation, 2 streak
        month_1 = 4
        month_2 = 5
        year = 2020

        report_of_day_1 = ObservationReportFactory(
            user=user,
            phone_upload_time=datetime(year, month_1, day_1, tzinfo=ZoneInfo("UTC")),
        )

        report_of_day_2 = ObservationReportFactory(
            user=user,
            phone_upload_time=datetime(year, month_2, day_2, tzinfo=ZoneInfo("UTC")),
        )

        self.assertEqual(
            Award.objects.filter(category__id=2).count(), 2
        )  # Daily participation given to each of the reports
        self.assertEqual(
            Award.objects.filter(category__id=3).count(), 1
        )  # Two day streak given to one of the reports
        self.assertEqual(
            Award.objects.filter(category__id=2).filter(report=report_of_day_1).count(),
            1,
        )  # Check each of the reports has first day
        self.assertEqual(
            Award.objects.filter(category__id=2).filter(report=report_of_day_2).count(),
            1,
        )
        self.assertEqual(
            Award.objects.filter(category__id=3).filter(report=report_of_day_2).count(),
            1,
        )  # Check second report has 2 day streak

    @staticmethod
    def get_notification_body_en(category_label, xp):
        context_en = {}
        context_en["amount_awarded"] = xp
        activate("en")
        context_en["reason_awarded"] = _(category_label)
        deactivate()
        return (
            render_to_string("awards/award_notification_en.html", context_en)
            .encode("ascii", "xmlcharrefreplace")
            .decode("UTF-8")
        )

    @staticmethod
    def get_notification_body_for_locale(category_label, xp, locale):
        context = {}
        context["amount_awarded"] = xp
        activate(locale)
        context["reason_awarded"] = _(category_label)
        deactivate()
        return (
            render_to_string("awards/award_notification_" + locale + ".html", context)
            .encode("ascii", "xmlcharrefreplace")
            .decode("UTF-8")
        )

    def test_10_report_achievement(self):
        user = TigaUserFactory()

        month_1 = 1
        year = 2020

        ObservationReportWithoutSignalFactory.create_batch(
            10,
            user=user,
            phone_upload_time=datetime(year, month_1, 1, tzinfo=ZoneInfo("UTC")),
        )

        self.assertEqual(
            Award.objects.filter(special_award_text="achievement_10_reports").count(), 1
        )  # Ten report achievement granted
        # emulate notifications
        if not settings.DISABLE_ACHIEVEMENT_NOTIFICATIONS:
            notification_body = self.get_notification_body_en(
                ACHIEVEMENT_10_REPORTS, ACHIEVEMENT_10_REPORTS_XP
            )
            self.assertEqual(
                Notification.objects.filter(
                    notification_content__body_html_en=notification_body
                ).count(),
                1,
            )

    def test_20_report_achievement(self):
        user = TigaUserFactory()

        month_1 = 1
        year = 2020

        ObservationReportWithoutSignalFactory.create_batch(
            20,
            user=user,
            phone_upload_time=datetime(year, month_1, 1, tzinfo=ZoneInfo("UTC")),
        )

        self.assertEqual(
            Award.objects.filter(special_award_text="achievement_10_reports").count(), 1
        )  # Ten report achievement granted
        self.assertEqual(
            Award.objects.filter(special_award_text="achievement_20_reports").count(), 1
        )  # Ten report achievement granted

        # emulate notifications
        if not settings.DISABLE_ACHIEVEMENT_NOTIFICATIONS:
            notification_body_10 = self.get_notification_body_en(
                ACHIEVEMENT_10_REPORTS, ACHIEVEMENT_10_REPORTS_XP
            )
            notification_body_20 = self.get_notification_body_en(
                ACHIEVEMENT_20_REPORTS, ACHIEVEMENT_20_REPORTS_XP
            )
            self.assertEqual(
                Notification.objects.filter(
                    notification_content__body_html_en=notification_body_10
                ).count(),
                1,
            )
            self.assertEqual(
                Notification.objects.filter(
                    notification_content__body_html_en=notification_body_20
                ).count(),
                1,
            )

    def test_50_report_achievement(self):
        user = TigaUserFactory()

        year = 2020

        ObservationReportWithoutSignalFactory.create_batch(
            50,
            user=user,
            phone_upload_time=datetime(year, 1, 1, tzinfo=ZoneInfo("UTC")),
        )

        self.assertEqual(
            Award.objects.filter(special_award_text="achievement_10_reports").count(), 1
        )  # Ten report achievement granted
        self.assertEqual(
            Award.objects.filter(special_award_text="achievement_20_reports").count(), 1
        )  # Ten report achievement granted
        self.assertEqual(
            Award.objects.filter(special_award_text="achievement_50_reports").count(), 1
        )  # Ten report achievement granted

        # emulate notifications
        if not settings.DISABLE_ACHIEVEMENT_NOTIFICATIONS:
            notification_body_10 = self.get_notification_body_en(
                ACHIEVEMENT_10_REPORTS, ACHIEVEMENT_10_REPORTS_XP
            )
            notification_body_20 = self.get_notification_body_en(
                ACHIEVEMENT_20_REPORTS, ACHIEVEMENT_20_REPORTS_XP
            )
            notification_body_50 = self.get_notification_body_en(
                ACHIEVEMENT_50_REPORTS, ACHIEVEMENT_50_REPORTS_XP
            )
            self.assertEqual(
                Notification.objects.filter(
                    notification_content__body_html_en=notification_body_10
                ).count(),
                1,
            )
            self.assertEqual(
                Notification.objects.filter(
                    notification_content__body_html_en=notification_body_20
                ).count(),
                1,
            )
            self.assertEqual(
                Notification.objects.filter(
                    notification_content__body_html_en=notification_body_50
                ).count(),
                1,
            )

    def test_corner_cases_first_of_season_different_users(self):
        user_1 = TigaUserFactory()
        user_2 = TigaUserFactory()

        day_1 = 30  # --> Daily participation, first of season
        month_1 = 4
        year = 2020

        report_1_user_1 = ObservationReportFactory(
            user=user_1,
            phone_upload_time=datetime(year, month_1, day_1, tzinfo=ZoneInfo("UTC")),
        )

        report_1_user_2 = ObservationReportFactory(
            user=user_2,
            phone_upload_time=datetime(year, month_1, day_1, tzinfo=ZoneInfo("UTC")),
        )

        self.assertEqual(
            Award.objects.filter(category__id=1).count(), 2
        )  # Daily participation given to each of the reports
        self.assertEqual(
            Award.objects.filter(category__id=2).count(), 2
        )  # First of season given to each of the reports
        self.assertEqual(
            Award.objects.filter(category__id=1).filter(report=report_1_user_1).count(),
            1,
        )
        self.assertEqual(
            Award.objects.filter(category__id=1).filter(report=report_1_user_2).count(),
            1,
        )

    def test_10_day_achievement_for_sq_locale(self):
        user = TigaUserFactory(locale="sq")

        month_1 = 1
        year = 2020

        ObservationReportWithoutSignalFactory.create_batch(
            10,
            user=user,
            phone_upload_time=datetime(year, month_1, 1, tzinfo=ZoneInfo("UTC")),
        )

        self.assertEqual(
            Award.objects.filter(special_award_text="achievement_10_reports").count(), 1
        )  # Ten report achievement granted
        # emulate notifications
        if not settings.DISABLE_ACHIEVEMENT_NOTIFICATIONS:
            notification_body = self.get_notification_body_for_locale(
                ACHIEVEMENT_10_REPORTS, ACHIEVEMENT_10_REPORTS_XP, "sq"
            )
            # The english notification should be in Albanian
            # for n in Notification.objects.all():
            #     print("<---- SEPARATOR ---->")
            #     print(n.notification_content.body_html_en)
            #     print("<---- END SEPARATOR ---->")
            self.assertEqual(
                Notification.objects.filter(
                    notification_content__body_html_sq=notification_body
                ).count(),
                1,
            )
