from tigaserver_app.models import Report, TigaUser
import csv

XP = 12
XP_REPORT_WITH_PICTURE = XP
XP_LOCATION = XP / 2

def compute_user_score_in_xp(user_uuid):
    user_reports = Report.objects.filter(user__user_UUID=user_uuid)
    user_reports_last_versions = filter(lambda x: x.latest_version, user_reports)
    user_reports_last_versions_photo = filter(lambda x: x.n_photos > 0, user_reports_last_versions)
    user_reports_last_versions_photo_located = filter(lambda x: x.located, user_reports_last_versions_photo)
    user_xp_reports_validation = 0
    for report in user_reports_last_versions_photo_located:
        report_classification = report.get_mean_combined_expert_adult_score()
        if report_classification['is_none'] == True and report_classification['score'] == -3.0:
            pass
        else:
            if report_classification['is_aegypti'] == True:
                user_xp_reports_validation += XP / 4
            else:
                user_xp_reports_validation += XP / 6

    user_xp_reports_picture = len(user_reports_last_versions_photo) * XP_REPORT_WITH_PICTURE
    user_xp_reports_picture_location = len(user_reports_last_versions_photo_located) * XP_LOCATION
    '''
    print( " XP for reports with picture - {0}".format( str(user_xp_reports_picture) ) )
    print( " XP for reports with picture and location - {0}".format( str( user_xp_reports_picture_location ) ) )
    print( " XP for validation - {0}".format(str(user_xp_reports_validation)))
    print( " Total XP - {0}".format(str(user_xp_reports_picture + user_xp_reports_picture_location + user_xp_reports_validation)))
    '''
    return user_xp_reports_picture + user_xp_reports_picture_location + user_xp_reports_validation

def score_comparison():
    with open('user_scores.csv', mode='w') as csvfile:
        users = TigaUser.objects.all()
        for user in users:
            xp_score = compute_user_score_in_xp(user.user_UUID)
            old_score = 0
            if user.profile:
                old_score = user.profile.score
            else:
                old_score = user.score
            csvfile_writer = csv.writer(csvfile, delimiter=',', quotechar='"')
            csvfile_writer.writerow([user.user_UUID, xp_score, old_score])