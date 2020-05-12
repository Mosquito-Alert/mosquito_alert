from tigaserver_app.models import Report, TigaUser
import csv
import time
import pandas as pd
import datetime

XP = 12
XP_REPORT_WITH_PICTURE = XP
XP_LOCATION = XP / 2

PICTURE_REWARD = 6
LOCATION_REWARD = 6
BITE_REWARD = 2

MOSQUITO_THORAX_QUESTION_REWARD = 2
MOSQUITO_ABDOMEN_QUESTION_REWARD = 2
MOSQUITO_LEG_QUESTION_REWARD = 2
SITE_WATER_QUESTION_REWARD = 4

MOSQUITO_HOW_LOOKS_QUESTION_ID = 7
MOSQUITO_THORAX_ANSWER_IDS = [711, 712, 713, 714]
MOSQUITO_ABDOMEN_ANSWER_IDS = [721, 722, 723, 724]
MOSQUITO_LEG_ANSWER_IDS = [731, 732, 733, 734]

SITE_WATER_QUESTION_ID = 10
SITE_WATER_ANSWER_IDS = [81, 101]

CULEX_CATEGORY_ID = 10
AEDES_CATEGORY_IDS = [4, 5, 6, 7]

'''
from tigaserver_app.models import TigaUser
#queryset to dataframe
df = pd.DataFrame(list(TigaUser.objects.all().values()))
#sort by scor
df.sort_values("score_v2", inplace=True)
#create rank column
df["rank"] = df["score_v2"].rank(ascending=False)
#get row by column value (in this case, user_uuid)
df.loc[df['user_UUID']=='b7853081-eea8-4f3f-abad-6192ba7e4429']
'''


'''
score metadata structure - json
{
    "user_uuid": x,
    "joined_label": x,
    "joined_value": x,
    "active_label": x,
    "active_value": x,
    "total_score": x,
    "overall_rank_value": x,
    "overall_class_value": x,
    "overall_class_label": x,
    "overall_perc": x,
    "score_detail":{
        "adult":{
            "score": x,
            "rank_value": x,
            "class_value": x,
            "class_label": x,
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


def is_water_answered(report):
    '''
    for response in report.responses:
        if response.question_id == SITE_WATER_QUESTION_ID and response.answer_id in SITE_WATER_ANSWERS_ID:
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


def get_user_class(max, min, user_score):
    if max == min:
        return {"value": 1, "label": "Novice"}
    if user_score == 0:
        return {"value": 1, "label": "Novice"}
    interval = (max - min)/5
    if min <= user_score <= interval * 1:
        return { "value": 1, "label": "Novice"}
    elif interval * 1 < user_score <= interval * 2:
        return { "value": 2, "label": "Contributor"}
    elif interval * 2 < user_score <= interval * 3:
        return { "value": 3, "label": "Expert"}
    elif interval * 3 < user_score <= interval * 4:
        return { "value": 4, "label": "Master"}
    else:
        return { "value": 5, "label": "Grandmaster"}

def get_min_max(sorted_dataframe, score_field_name):
    max_score = sorted_dataframe[score_field_name].max()
    min_score = sorted_dataframe[score_field_name].min()
    # get row by column value (in this case, user_uuid)
    # df.loc[df['user_UUID'] == 'b7853081-eea8-4f3f-abad-6192ba7e4429']
    return {"min": min_score, "max": max_score}


def get_user_rank_value(sorted_dataframe, user_UUID):
    subdf = sorted_dataframe.loc[sorted_dataframe['user_UUID'] == user_UUID]['rank']
    if subdf.empty:
        return 0
    return int(subdf.iloc[0])

def get_bite_report_score(report, result):
    local_result = {}
    local_result['report'] = report.version_UUID
    local_result['report_date'] = report.server_upload_time.strftime("%d/%m/%Y")
    local_result['report_score'] = 0
    local_result['awards'] = []
    local_result['awards'].append({"reason": "bite_report", "xp_awarded": BITE_REWARD})
    local_result['report_score'] = BITE_REWARD
    result['score_detail']['bite']['score_items'].append(local_result)
    return result


def get_site_report_score(report, result):
    local_result = {}
    local_result['report'] = report.version_UUID
    local_result['report_date'] = report.server_upload_time.strftime("%d/%m/%Y")
    picture = report.get_final_photo_html()
    if picture:
        local_result['report_photo'] = picture.photo.url.replace('tigapics/', 'tigapics_small/')
    else:
        local_result['report_photo'] = None
    local_result['report_score'] = 0
    local_result['awards'] = []
    if report.n_photos > 0:
        local_result['awards'].append({"reason": "picture", "xp_awarded": PICTURE_REWARD})
        local_result['report_score'] += PICTURE_REWARD
    if report.located:
        local_result['awards'].append({"reason": "location", "xp_awarded": LOCATION_REWARD})
        local_result['report_score'] += LOCATION_REWARD
    if is_water_answered(report):
        local_result['awards'].append({"reason": "water_question", "xp_awarded": SITE_WATER_QUESTION_REWARD})
        local_result['report_score'] += SITE_WATER_QUESTION_REWARD
    result['score_detail']['site']['score_items'].append(local_result)
    return result


def get_adult_report_score(report, result):
    validation_result = report.get_final_combined_expert_category_euro_struct()
    local_result = {}
    local_result['report'] = report.version_UUID
    local_result['report_date'] = report.server_upload_time.strftime("%d/%m/%Y")
    picture = report.get_final_photo_html()
    if picture:
        local_result['report_photo'] = picture.photo.url.replace('tigapics/', 'tigapics_small/')
    else:
        local_result['report_photo'] = None
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


def diff_month( date_now, date_before ):
    return ( date_now.year - date_before.year ) * 12 + date_now.month - date_now.month


def get_elapsed_label( date_now, date_before ):
    diff = date_now - date_before
    if diff.days >= 30:
        diff_months = diff_month( date_now, date_before )
        if diff_months > 12:
            return str( diff_months / 12 ) + " years ago"
        else:
            return str( diff_months ) + " months ago"
    else:
        return str(diff.days) + " days ago"


def compute_user_score_in_xp_v2_fast(user_uuid):

    result = {}
    result['total_score'] = 0
    result['user_uuid'] = user_uuid
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

    adult_score = 0
    for report in adult_last_versions:
        result = get_adult_report_score(report, result)
        index = len(result['score_detail']['adult']['score_items']) - 1
        result['score_detail']['adult']['score'] += result['score_detail']['adult']['score_items'][index][
            'report_score']
        adult_score += result['score_detail']['adult']['score_items'][index]['report_score']
    result['total_score'] += adult_score

    results_bite = {}
    results_bite['score'] = 0
    results_bite['score_items'] = []
    result['score_detail']['bite'] = results_bite

    bite_score = 0
    for report in bites:
        result = get_bite_report_score(report, result)
        index = len(result['score_detail']['bite']['score_items']) - 1
        result['score_detail']['bite']['score'] += result['score_detail']['bite']['score_items'][index]['report_score']
        bite_score += result['score_detail']['bite']['score_items'][index]['report_score']
    result['total_score'] += bite_score

    results_site = {}
    results_site['score'] = 0
    results_site['score_items'] = []
    result['score_detail']['site'] = results_site

    site_score = 0
    for report in sites:
        result = get_site_report_score(report, result)
        index = len(result['score_detail']['site']['score_items']) - 1
        result['score_detail']['site']['score'] += result['score_detail']['site']['score_items'][index]['report_score']
        site_score += result['score_detail']['site']['score_items'][index]['report_score']
    result['total_score'] += site_score

    return result


def compute_user_score_in_xp_v2(user_uuid):

    qs_overall = TigaUser.objects.exclude(score_v2=0)
    qs_adult = TigaUser.objects.exclude(score_v2_adult=0)
    qs_site = TigaUser.objects.exclude(score_v2_site=0)
    qs_bite = TigaUser.objects.exclude(score_v2_bite=0)

    overall_df = pd.DataFrame(list(qs_overall.values_list('score_v2', 'user_UUID')), columns=['score_v2', 'user_UUID'])
    adult_df = pd.DataFrame(list(qs_adult.values_list('score_v2_adult', 'user_UUID')), columns=['score_v2_adult', 'user_UUID'])
    site_df = pd.DataFrame(list(qs_site.values_list('score_v2_site', 'user_UUID')), columns=['score_v2_site', 'user_UUID'])
    bite_df = pd.DataFrame(list(qs_bite.values_list('score_v2_bite', 'user_UUID')), columns=['score_v2_bite', 'user_UUID'])

    overall_sorted_df = overall_df.sort_values('score_v2', inplace=False)
    overall_sorted_df["rank"] = overall_sorted_df['score_v2'].rank(method='dense', ascending=False)

    adult_sorted_df = adult_df.sort_values('score_v2_adult', inplace=False)
    adult_sorted_df["rank"] = adult_sorted_df['score_v2_adult'].rank(method='dense', ascending=False)

    site_sorted_df = site_df.sort_values('score_v2_site', inplace=False)
    site_sorted_df["rank"] = site_sorted_df['score_v2_site'].rank(method='dense', ascending=False)

    bite_sorted_df = bite_df.sort_values('score_v2_bite', inplace=False)
    bite_sorted_df["rank"] = bite_sorted_df['score_v2_bite'].rank(method='dense', ascending=False)

    result = {}
    result['total_score'] = 0
    result['user_uuid'] = user_uuid
    result['score_detail'] = {}

    rank_value_overall = get_user_rank_value(overall_sorted_df, user_uuid)
    min_max_overall = get_min_max(overall_sorted_df, 'score_v2')
    result['overall_rank_value'] = rank_value_overall

    rank_value_adult = get_user_rank_value(adult_sorted_df, user_uuid)
    min_max_adult = get_min_max(adult_sorted_df, 'score_v2_adult')

    rank_value_site = get_user_rank_value(site_sorted_df, user_uuid)
    min_max_site = get_min_max(site_sorted_df, 'score_v2_site')

    rank_value_bite = get_user_rank_value(bite_sorted_df, user_uuid)
    min_max_bite = get_min_max(bite_sorted_df, 'score_v2_bite')

    current_date = datetime.date.today()
    try:
        user = TigaUser.objects.get(pk=user_uuid)
        result['joined_value'] = user.registration_time.strftime("%d/%m/%Y")
        result['joined_label'] = get_elapsed_label(current_date, user.registration_time.date())
    except TigaUser.DoesNotExist:
        result['joined_value'] = None
    user_reports = Report.objects.filter(user__user_UUID=user_uuid).order_by('-creation_time')

    if user_reports:
        result['active_value'] = user_reports[0].creation_time.strftime("%d/%m/%Y")
        result['active_label'] = get_elapsed_label(current_date, user_reports[0].creation_time.date())
    else:
        result['active_value'] = None
        result['active_label'] = None

    adults = user_reports.filter(type='adult')
    bites = user_reports.filter(type='bite')
    sites = user_reports.filter(type='site')

    adult_last_versions = filter(lambda x: x.latest_version, adults)

    results_adult = {}
    results_adult['score'] = 0
    results_adult['score_items'] = []
    result['score_detail']['adult'] = results_adult

    adult_score = 0
    for report in adult_last_versions:
        result = get_adult_report_score(report, result)
        index = len(result['score_detail']['adult']['score_items']) - 1
        result['score_detail']['adult']['score'] += result['score_detail']['adult']['score_items'][index]['report_score']
        adult_score += result['score_detail']['adult']['score_items'][index]['report_score']
    result['total_score'] += adult_score

    results_bite = {}
    results_bite['score'] = 0
    results_bite['score_items'] = []
    result['score_detail']['bite'] = results_bite

    bite_score = 0
    for report in bites:
        result = get_bite_report_score(report, result)
        index = len(result['score_detail']['bite']['score_items']) - 1
        result['score_detail']['bite']['score'] += result['score_detail']['bite']['score_items'][index]['report_score']
        bite_score += result['score_detail']['bite']['score_items'][index]['report_score']
    result['total_score'] += bite_score

    results_site = {}
    results_site['score'] = 0
    results_site['score_items'] = []
    result['score_detail']['site'] = results_site

    site_score = 0
    for report in sites:
        result = get_site_report_score(report, result)
        index = len(result['score_detail']['site']['score_items']) - 1
        result['score_detail']['site']['score'] += result['score_detail']['site']['score_items'][index]['report_score']
        site_score += result['score_detail']['site']['score_items'][index]['report_score']
    result['total_score'] += site_score


    overall_class = get_user_class(min_max_overall['max'], min_max_overall['min'], result['total_score'])
    result['overall_class_value'] = overall_class['value']
    result['overall_class_label'] = overall_class['label']

    adult_class = get_user_class(min_max_adult['max'], min_max_adult['min'], result['score_detail']['adult']['score'])
    result['score_detail']['adult']['class_value'] = adult_class['value']
    result['score_detail']['adult']['class_label'] = adult_class['label']
    result['score_detail']['adult']['rank_value'] = rank_value_adult

    site_class = get_user_class(min_max_site['max'], min_max_site['min'], result['score_detail']['site']['score'])
    result['score_detail']['site']['class_value'] = site_class['value']
    result['score_detail']['site']['class_label'] = site_class['label']
    result['score_detail']['site']['rank_value'] = rank_value_site

    bite_class = get_user_class(min_max_bite['max'], min_max_bite['min'], result['score_detail']['bite']['score'])
    result['score_detail']['bite']['class_value'] = bite_class['value']
    result['score_detail']['bite']['class_label'] = bite_class['label']
    result['score_detail']['bite']['rank_value'] = rank_value_bite

    overall_number_below_rank = overall_sorted_df[ overall_sorted_df['rank'] <= result['overall_rank_value'] ].count()['rank']
    overall_number_total = overall_sorted_df.count()['rank']

    adult_number_below_rank = adult_sorted_df[adult_sorted_df['rank'] <= result['score_detail']['adult']['rank_value']].count()['rank']
    adult_number_total = adult_sorted_df.count()['rank']

    site_number_below_rank = site_sorted_df[site_sorted_df['rank'] <= result['score_detail']['site']['rank_value']].count()['rank']
    site_number_total = site_sorted_df.count()['rank']

    bite_number_below_rank = bite_sorted_df[bite_sorted_df['rank'] <= result['score_detail']['bite']['rank_value']].count()['rank']
    bite_number_total = bite_sorted_df.count()['rank']

    result['overall_top_perc'] = (float(overall_number_below_rank)/float(overall_number_total)) * 100.0
    result['overall_ranked_users'] = overall_number_total

    if adult_number_below_rank == 0 and adult_number_total == 0:
        result['score_detail']['adult']['top_perc'] = 100.0
    else:
        result['score_detail']['adult']['top_perc'] = (float(adult_number_below_rank) / float(adult_number_total)) * 100.0
    result['score_detail']['adult']['ranked_users'] = adult_number_total

    if site_number_below_rank == 0 and site_number_total == 0:
        result['score_detail']['site']['top_perc'] = 100.0
    else:
        result['score_detail']['site']['top_perc'] = (float(site_number_below_rank) / float(site_number_total)) * 100.0
    result['score_detail']['site']['ranked_users'] = site_number_total

    if bite_number_below_rank == 0 and bite_number_total == 0:
        result['score_detail']['bite']['top_perc'] = 100.0
    else:
        result['score_detail']['bite']['top_perc'] = (float(bite_number_below_rank) / float(bite_number_total)) * 100.0
    result['score_detail']['bite']['ranked_users'] = bite_number_total

    return result


def get_ranking_data( date_ini=None, date_end=datetime.datetime.today() ):
    retval = {}
    qs_reports = Report.objects.filter(creation_time__lte=datetime.datetime.today())
    if date_ini is not None:
        qs_reports = qs_reports.filter( creation_time__gte=date_ini )
    users_for_reports = qs_reports.values('user').distinct()
    qs_overall = TigaUser.objects.exclude(score_v2=0)
    overall_df = pd.DataFrame(list(qs_overall.values_list('score_v2', 'user_UUID')), columns=['score_v2', 'user_UUID'])
    overall_sorted_df = overall_df.sort_values('score_v2', inplace=False)
    overall_sorted_df["rank"] = overall_sorted_df['score_v2'].rank(method='dense', ascending=False)
    overall_sorted_df.sort_values('rank', inplace=True)
    retval['data'] = []
    for index, row in overall_sorted_df.iterrows():
        retval['data'].append( { "score_v2": row['score_v2'],"user_uuid":row['user_UUID'],"rank":row['rank']} )
    return retval


def compute_all_user_scores():
    all_users = TigaUser.objects.all()
    for user in all_users:
        score = compute_user_score_in_xp_v2( user.user_UUID )
        user.score_v2 = score
        user.save()

