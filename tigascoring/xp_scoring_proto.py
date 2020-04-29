from tigaserver_app.models import Report, TigaUser
import csv

XP = 12
XP_REPORT_WITH_PICTURE = XP
XP_LOCATION = XP / 2

PICTURE_REWARD = 6
LOCATION_REWARD = 6

MOSQUITO_THORAX_QUESTION_REWARD = 2
MOSQUITO_ABDOMEN_QUESTION_REWARD = 2
MOSQUITO_LEG_QUESTION_REWARD = 2

MOSQUITO_HOW_LOOKS_QUESTION_ID = 7
MOSQUITO_THORAX_ANSWER_IDS = [711, 712, 713, 714]
MOSQUITO_ABDOMEN_ANSWER_IDS = [721, 722, 723, 724]
MOSQUITO_LEG_ANSWER_IDS = [731, 732, 733, 734]
CULEX_CATEGORY_ID = 10
AEDES_CATEGORY_IDS = [4, 5, 6, 7]


def is_thorax_answered(report):
    '''
    for response in report.responses:
        if response.question_id == MOSQUITO_HOW_LOOKS_QUESTION_ID and response.answer_id in MOSQUITO_THORAX_ANSWER_IDS:
            return True
    '''
    return False


def is_abdomen_answered(report):
    '''
    for response in report.responses:
        if response.question_id == MOSQUITO_HOW_LOOKS_QUESTION_ID and response.answer_id in MOSQUITO_ABDOMEN_ANSWER_IDS:
            return True
    '''
    return False


def is_leg_answered(report):
    '''
    for response in report.responses:
        if response.question_id == MOSQUITO_HOW_LOOKS_QUESTION_ID and response.answer_id in MOSQUITO_LEG_ANSWER_IDS:
            return True
    '''
    return False


def is_culex(validation_result):
    if validation_result['category'] is not None:
        if validation_result['category'].id == CULEX_CATEGORY_ID:
            return True
    return False


def is_aedes(validation_result):
    if validation_result['category'] is not None:
        if validation_result['category'].id in AEDES_CATEGORY_IDS:
            return True
    return False


def get_adult_report_score(report):
    score = 0
    validation_result = report.get_final_combined_expert_category_euro_struct()
    if is_culex(validation_result) or is_aedes(validation_result):
        if report.n_photos > 0:
            score += PICTURE_REWARD
        if report.located:
            score += LOCATION_REWARD
    elif is_aedes(validation_result):
        if is_thorax_answered(report):
            score += MOSQUITO_THORAX_QUESTION_REWARD
        if is_abdomen_answered(report):
            score += MOSQUITO_ABDOMEN_QUESTION_REWARD
        if is_leg_answered(report):
            score += MOSQUITO_LEG_QUESTION_REWARD
    return score


def compute_user_score_in_xp_v2(user_uuid):
    user_reports = Report.objects.filter(user__user_UUID=user_uuid)

    adults = user_reports.filter(type='adult')
    bites = user_reports.filter(type='bite')
    sites = user_reports.filter(type='site')

    adult_last_versions = filter(lambda x: x.latest_version, adults)

    for report in adult_last_versions:
        print( "{0} - {1}".format( report.version_UUID, get_adult_report_score(report) ) )



'''
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
    
    #print( " XP for reports with picture - {0}".format( str(user_xp_reports_picture) ) )
    #print( " XP for reports with picture and location - {0}".format( str( user_xp_reports_picture_location ) ) )
    #print( " XP for validation - {0}".format(str(user_xp_reports_validation)))
    #print( " Total XP - {0}".format(str(user_xp_reports_picture + user_xp_reports_picture_location + user_xp_reports_validation)))
    
    return user_xp_reports_picture + user_xp_reports_picture_location + user_xp_reports_validation
'''

'''
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
'''