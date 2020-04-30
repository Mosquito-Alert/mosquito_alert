from tigaserver_app.models import Report, TigaUser
import csv
import time

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


'''
score metadata structure - json
{
    "total_score": x,
    "score_detail":{
        "adult":{
            "score": x,
            "score_items": [
                {
                    "report": xxxxx,
                    "report_score": xxxx,
                    "awards": [
                        "reason":,
                        "xp_awarded":
                    ],
                }
            ]
        },
        "bite":{
        },
        "site":{
        },
        "awards":{
        }
    }
}
'''


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


def get_adult_report_score(report, result):
    validation_result = report.get_final_combined_expert_category_euro_struct()
    local_result = {}
    local_result['report'] = report.version_UUID
    local_result['report_date'] = report.server_upload_time
    local_result['report_score'] = 0
    local_result['awards'] = []
    if is_culex(validation_result) or is_aedes(validation_result):
        if report.n_photos > 0:
            local_result['awards'].append({ "reason": "picture", "xp_awarded": PICTURE_REWARD })
            local_result['report_score'] += PICTURE_REWARD
        if report.located:
            local_result['awards'].append({"reason": "location", "xp_awarded": LOCATION_REWARD })
            local_result['report_score'] += LOCATION_REWARD
    elif is_aedes(validation_result):
        if is_thorax_answered(report):
            local_result['awards'].append({"reason": "thorax_question", "xp_awarded": MOSQUITO_THORAX_QUESTION_REWARD})
            local_result['report_score'] += MOSQUITO_THORAX_QUESTION_REWARD
        if is_abdomen_answered(report):
            local_result['awards'].append({"reason": "abdomen_question", "xp_awarded": MOSQUITO_ABDOMEN_QUESTION_REWARD})
            local_result['report_score'] += MOSQUITO_ABDOMEN_QUESTION_REWARD
        if is_leg_answered(report):
            local_result['awards'].append({"reason": "leg_question", "xp_awarded": MOSQUITO_LEG_QUESTION_REWARD})
            local_result['report_score'] += MOSQUITO_LEG_QUESTION_REWARD
    result['score_detail']['adult']['score_items'].append(local_result)
    return result


def compute_user_score_in_xp_v2(user_uuid):
    result = {}
    result['total_score'] = 0
    result['score_detail'] = {}
    user_reports = Report.objects.filter(user__user_UUID=user_uuid).order_by('-creation_time')

    adults = user_reports.filter(type='adult')
    bites = user_reports.filter(type='bite')
    sites = user_reports.filter(type='site')

    adult_last_versions = filter(lambda x: x.latest_version, adults)

    results_adult = {}
    results_adult['score'] = 0
    results_adult['score_items'] = []
    result['score_detail']['adult'] = results_adult

    total_score = 0
    for report in adult_last_versions:
        result = get_adult_report_score(report, result)
        index = len(result['score_detail']['adult']['score_items']) - 1
        result['score_detail']['adult']['score'] += result['score_detail']['adult']['score_items'][index]['report_score']
        total_score += result['score_detail']['adult']['score_items'][index]['report_score']
    result['total_score'] = total_score
    return result


def compute_all_user_scores():
    all_users = TigaUser.objects.all()
    for user in all_users:
        score = compute_user_score_in_xp_v2( user.user_UUID )
        user.score_v2 = score
        user.save()

def compute_all_scores():
    all_users = TigaUser.objects.all()
    result_table = []
    max_score = 0
    max_user = -1
    start_time = time.time()
    print("Starting...")
    for user in all_users:
        score = compute_user_score_in_xp_v2(user.user_UUID)
        if score >= max_score:
            max_score = score
            max_user = user.user_UUID
        result_table.append([user.user_UUID, score])
    elapsed_time = time.time() - start_time
    print("Finished in {0}".format(elapsed_time))
