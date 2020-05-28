from tigaserver_app.models import AwardCategory, Award


def grant_first_of_season( report, granter ):
    c = AwardCategory.objects.get(category_label='start_of_season')
    grant_award( report, report.creation_time, report.user, granter, c )


def grant_first_of_day( report, granter ):
    c = AwardCategory.objects.get(category_label='daily_participation')
    grant_award( report, report.creation_time, report.user, granter, c )


def grant_two_consecutive_days_sending( report, granter ):
    c = AwardCategory.objects.get(category_label='fidelity_day_2')
    grant_award( report, report.creation_time, report.user, granter, c )


def grant_three_consecutive_days_sending(report, granter):
        c = AwardCategory.objects.get(category_label='fidelity_day_3')
        grant_award(report, report.creation_time, report.user, granter, c)


def grant_award(for_report, awarded_on_date, awarded_to_tigauser, awarded_by_expert, award_category):
    '''

    :param for_report: Report for which the award is given
    :param awarded_on_date: Date on which the award was granted (usually same as report_creation)
    :param awarded_to_tigauser: User to which it was awarded (usually report owner)
    :param awarded_by_expert: Expert which awarded the report
    :param award_category: Category of the award
    :return:
    '''
    a = Award()
    a.report = for_report
    a.date_given = awarded_on_date
    a.given_to = awarded_to_tigauser
    if awarded_by_expert is not None:
        a.expert = awarded_by_expert
    if award_category is not None:
        a.category = award_category
    a.save()