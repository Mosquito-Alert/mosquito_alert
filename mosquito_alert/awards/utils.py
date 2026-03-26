from datetime import timedelta

from .models import Award, AwardCategory


ACHIEVEMENT_10_REPORTS = "achievement_10_reports"
ACHIEVEMENT_20_REPORTS = "achievement_20_reports"
ACHIEVEMENT_50_REPORTS = "achievement_50_reports"
DAILY_PARTICIPATION = "daily_participation"
START_OF_SEASON = "start_of_season"
FIDELITY_DAY_2 = "fidelity_day_2"
FIDELITY_DAY_3 = "fidelity_day_3"
ACHIEVEMENT_10_REPORTS_XP = 10
ACHIEVEMENT_20_REPORTS_XP = 20
ACHIEVEMENT_50_REPORTS_XP = 50


def one_day_between_and_same_week(r1_date_less_recent, r2_date_most_recent):
    day_before = r2_date_most_recent - timedelta(days=1)
    week_less_recent = r1_date_less_recent.isocalendar()[1]
    week_most_recent = r2_date_most_recent.isocalendar()[1]
    return (
        day_before.year == r1_date_less_recent.year
        and day_before.month == r1_date_less_recent.month
        and day_before.day == r1_date_less_recent.day
        and week_less_recent == week_most_recent
    )


def grant_10_reports_achievement(report, granter):
    grant_special_award(
        None,
        report.creation_time,
        report.user,
        granter,
        ACHIEVEMENT_10_REPORTS,
        ACHIEVEMENT_10_REPORTS_XP,
    )


def grant_20_reports_achievement(report, granter):
    grant_special_award(
        None,
        report.creation_time,
        report.user,
        granter,
        ACHIEVEMENT_20_REPORTS,
        ACHIEVEMENT_20_REPORTS_XP,
    )


def grant_50_reports_achievement(report, granter):
    grant_special_award(
        None,
        report.creation_time,
        report.user,
        granter,
        ACHIEVEMENT_50_REPORTS,
        ACHIEVEMENT_50_REPORTS_XP,
    )


def grant_first_of_season(report, granter):
    if c := AwardCategory.objects.filter(category_label=START_OF_SEASON).first():
        grant_award(report, report.creation_time, report.user, granter, c)


def grant_first_of_day(report, granter):
    if c := AwardCategory.objects.filter(category_label=DAILY_PARTICIPATION).first():
        grant_award(report, report.creation_time, report.user, granter, c)


def grant_two_consecutive_days_sending(report, granter):
    if c := AwardCategory.objects.filter(category_label=FIDELITY_DAY_2).first():
        grant_award(report, report.creation_time, report.user, granter, c)


def grant_three_consecutive_days_sending(report, granter):
    if c := AwardCategory.objects.filter(category_label=FIDELITY_DAY_3).first():
        grant_award(report, report.creation_time, report.user, granter, c)


def grant_special_award(
    for_report,
    awarded_on_date,
    awarded_to_tigauser,
    awarded_by_expert,
    special_award_label,
    special_award_xp,
):
    """
    :param for_report: Optional
    :param awarded_on_date: Mandatory
    :param awarded_to_tigauser: Mandatory
    :param awarded_by_expert: Mandatory
    :param special_award_label: Mandatory
    :param special_award_xp: Mandatory
    :return:
    """
    a = Award()
    a.report = for_report
    a.date_given = awarded_on_date
    a.given_to = awarded_to_tigauser
    if awarded_by_expert is not None:
        a.expert = awarded_by_expert
    a.special_award_text = special_award_label
    a.special_award_xp = special_award_xp
    a.save()


def grant_award(
    for_report, awarded_on_date, awarded_to_tigauser, awarded_by_expert, award_category
):
    """

    :param for_report: Report for which the award is given
    :param awarded_on_date: Date on which the award was granted (usually same as report_creation)
    :param awarded_to_tigauser: User to which it was awarded (usually report owner)
    :param awarded_by_expert: Expert which awarded the report
    :param award_category: Category of the award
    :return:
    """
    a = Award()
    a.report = for_report
    a.date_given = awarded_on_date
    a.given_to = awarded_to_tigauser
    if awarded_by_expert is not None:
        a.expert = awarded_by_expert
    if award_category is not None:
        a.category = award_category
    a.save()
